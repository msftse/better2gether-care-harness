using Microsoft.Bot.Builder;
using Microsoft.Bot.Schema;
using Microsoft.Extensions.Logging;
using CareAgentTeamsBridge.Models;
using CareAgentTeamsBridge.Services;

namespace CareAgentTeamsBridge.Bot;

public sealed class CareAgentBot(
    CareQueue queue,
    SessionMapStore sessionMap,
    ILogger<CareAgentBot> logger) : ActivityHandler
{
    protected override async Task OnMessageActivityAsync(
        ITurnContext<IMessageActivity> turnContext,
        CancellationToken cancellationToken)
    {
        var prompt = RemoveBotMention(turnContext.Activity).Trim();
        var startsNewSession = prompt.Equals("/start", StringComparison.OrdinalIgnoreCase) ||
            prompt.StartsWith("/start ", StringComparison.OrdinalIgnoreCase);
        if (startsNewSession)
        {
            prompt = prompt["/start".Length..].Trim();
            await sessionMap.DeleteAsync(turnContext.Activity.GetConversationReference(), cancellationToken);
            if (string.IsNullOrWhiteSpace(prompt))
            {
                await turnContext.SendActivityAsync(
                    "Started a fresh Care Copilot conversation.",
                    cancellationToken: cancellationToken);
                return;
            }
        }

        if (string.IsNullOrWhiteSpace(prompt))
        {
            await turnContext.SendActivityAsync(
                "Tag me with a care question, for example: `@Care Copilot how many SPO2-CRIT alerts fired, broken down by region?`",
                cancellationToken: cancellationToken);
            return;
        }

        var activity = turnContext.Activity;
        var job = new CareJob(
            prompt,
            activity.From?.AadObjectId ?? activity.From?.Id ?? "teams-user",
            activity.From?.Name ?? "Teams user",
            activity.GetConversationReference(),
            startsNewSession);

        await queue.EnqueueAsync(job, cancellationToken);
        await turnContext.SendActivityAsync(
            "On it — asking the care agent (Genie + care KB). This usually takes under a minute.",
            cancellationToken: cancellationToken);
        logger.LogInformation(
            "Queued care question for Teams conversation {ConversationId}",
            activity.Conversation?.Id);
    }

    protected override async Task OnMembersAddedAsync(
        IList<ChannelAccount> membersAdded,
        ITurnContext<IConversationUpdateActivity> turnContext,
        CancellationToken cancellationToken)
    {
        foreach (var member in membersAdded.Where(member => member.Id != turnContext.Activity.Recipient?.Id))
        {
            await turnContext.SendActivityAsync(
                "Hi! I'm the Better2gether Care Copilot. Ask me about member vitals, alerts, device "
                + "troubleshooting, or program policy — I combine live fleet data (Databricks Genie) with "
                + "the care knowledge base. Try: `how many SPO2-CRIT alerts by region?`",
                cancellationToken: cancellationToken);
        }
    }

    private static string RemoveBotMention(IMessageActivity activity)
    {
        var text = activity.Text ?? string.Empty;
        var mentions = activity.Entities?
            .Where(entity => string.Equals(entity.Type, "mention", StringComparison.OrdinalIgnoreCase))
            .Select(entity => entity.GetAs<Mention>())
            .Where(mention => mention?.Mentioned?.Id == activity.Recipient?.Id)
            .ToList() ?? [];

        return mentions.Aggregate(text, (current, mention) =>
            string.IsNullOrWhiteSpace(mention.Text)
                ? current
                : current.Replace(mention.Text, string.Empty, StringComparison.OrdinalIgnoreCase));
    }
}
