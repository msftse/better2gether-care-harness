using Microsoft.Azure.Functions.Worker;
using Microsoft.Bot.Builder;
using Microsoft.Bot.Builder.Integration.AspNet.Core;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using CareAgentTeamsBridge.Models;
using CareAgentTeamsBridge.Services;

namespace CareAgentTeamsBridge.Functions;

public sealed class CareWorker(
    FoundryAgentClient foundryAgent,
    SessionMapStore sessionMap,
    CloudAdapter adapter,
    IConfiguration configuration,
    ILogger<CareWorker> logger)
{
    [Function("ProcessCareQuestion")]
    public async Task Run(
        [QueueTrigger(CareQueue.QueueName, Connection = "AzureWebJobsStorage")] string payload,
        CancellationToken cancellationToken)
    {
        var job = JsonConvert.DeserializeObject<CareJob>(payload)
            ?? throw new InvalidOperationException("The queued care question payload is invalid.");

        string reply;
        try
        {
            var previousResponseId = job.StartNewSession
                ? null
                : await sessionMap.GetResponseIdAsync(job.ConversationReference, cancellationToken);
            var result = await foundryAgent.RespondAsync(job.Prompt, previousResponseId, cancellationToken);
            if (!string.IsNullOrEmpty(result.ResponseId))
            {
                await sessionMap.SetResponseIdAsync(job.ConversationReference, result.ResponseId, cancellationToken);
            }
            reply = Truncate(result.Response);
        }
        catch (Exception exception)
        {
            logger.LogError(
                exception,
                "Care question failed for {ConversationId}",
                job.ConversationReference.Conversation?.Id);
            reply = "The care agent couldn't complete that question. Check the bridge's Application Insights logs and try again.";
        }

        var appId = configuration["MicrosoftAppId"]
            ?? throw new InvalidOperationException("MicrosoftAppId is not configured.");

        await adapter.ContinueConversationAsync(
            appId,
            job.ConversationReference,
            async (turnContext, token) => await turnContext.SendActivityAsync(reply, cancellationToken: token),
            cancellationToken);
    }

    private static string Truncate(string response) =>
        response.Length <= 24000
            ? response
            : string.Concat(response.AsSpan(0, 24000), "\n\n_Response truncated._");
}
