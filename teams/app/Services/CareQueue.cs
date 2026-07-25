using Azure.Storage.Queues;
using Azure.Storage.Queues.Models;
using Microsoft.Extensions.Configuration;
using Newtonsoft.Json;
using CareAgentTeamsBridge.Models;

namespace CareAgentTeamsBridge.Services;

public sealed class CareQueue
{
    public const string QueueName = "care-questions";

    private readonly QueueClient _queue;

    public CareQueue(IConfiguration configuration)
    {
        var connectionString = configuration["AzureWebJobsStorage"]
            ?? throw new InvalidOperationException("AzureWebJobsStorage is not configured.");
        _queue = new QueueClient(
            connectionString,
            QueueName,
            new QueueClientOptions { MessageEncoding = QueueMessageEncoding.Base64 });
    }

    public async Task EnqueueAsync(CareJob job, CancellationToken cancellationToken)
    {
        await _queue.CreateIfNotExistsAsync(cancellationToken: cancellationToken);
        await _queue.SendMessageAsync(JsonConvert.SerializeObject(job), cancellationToken);
    }
}
