using Microsoft.Bot.Schema;

namespace CareAgentTeamsBridge.Models;

public sealed record CareJob(
    string Prompt,
    string UserId,
    string DisplayName,
    ConversationReference ConversationReference,
    bool StartNewSession = false);

public sealed record CareResult(
    string? ResponseId,
    string Response);
