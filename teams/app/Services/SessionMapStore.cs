using System.Security.Cryptography;
using System.Text;
using Azure;
using Azure.Data.Tables;
using Microsoft.Bot.Schema;
using Microsoft.Extensions.Configuration;

namespace CareAgentTeamsBridge.Services;

/// <summary>
/// Maps a Teams conversation to the last Foundry response id, so follow-up
/// questions chain through `previous_response_id` and keep conversational
/// context on the hosted agent's server-side session storage.
/// </summary>
public sealed class SessionMapStore
{
    private const string PartitionKey = "teams-conversations";
    private readonly TableClient _table;

    public SessionMapStore(IConfiguration configuration)
    {
        var connectionString = configuration["AzureWebJobsStorage"]
            ?? throw new InvalidOperationException("AzureWebJobsStorage is not configured.");
        var tableName = configuration["SESSION_MAP_TABLE"] ?? "sessionmap";
        _table = new TableClient(connectionString, tableName);
    }

    public async Task<string?> GetResponseIdAsync(
        ConversationReference conversationReference,
        CancellationToken cancellationToken)
    {
        try
        {
            var response = await _table.GetEntityAsync<SessionMapEntity>(
                PartitionKey,
                CreateRowKey(conversationReference),
                cancellationToken: cancellationToken);
            return response.Value.ResponseId;
        }
        catch (RequestFailedException exception) when (exception.Status == 404)
        {
            return null;
        }
    }

    public async Task SetResponseIdAsync(
        ConversationReference conversationReference,
        string responseId,
        CancellationToken cancellationToken)
    {
        await _table.CreateIfNotExistsAsync(cancellationToken);
        await _table.UpsertEntityAsync(
            new SessionMapEntity
            {
                PartitionKey = PartitionKey,
                RowKey = CreateRowKey(conversationReference),
                ResponseId = responseId,
                ConversationId = conversationReference.Conversation?.Id,
                ChannelId = conversationReference.ChannelId
            },
            TableUpdateMode.Replace,
            cancellationToken);
    }

    public async Task DeleteAsync(
        ConversationReference conversationReference,
        CancellationToken cancellationToken)
    {
        try
        {
            await _table.DeleteEntityAsync(
                PartitionKey,
                CreateRowKey(conversationReference),
                ETag.All,
                cancellationToken);
        }
        catch (RequestFailedException exception) when (exception.Status == 404)
        {
        }
    }

    private static string CreateRowKey(ConversationReference conversationReference)
    {
        var identity = $"{conversationReference.ChannelId}|{conversationReference.Conversation?.Id}";
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(identity))).ToLowerInvariant();
    }

    private sealed class SessionMapEntity : ITableEntity
    {
        public string PartitionKey { get; set; } = string.Empty;
        public string RowKey { get; set; } = string.Empty;
        public DateTimeOffset? Timestamp { get; set; }
        public ETag ETag { get; set; }
        public string ResponseId { get; set; } = string.Empty;
        public string? ConversationId { get; set; }
        public string? ChannelId { get; set; }
    }
}
