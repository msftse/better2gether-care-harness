using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Azure.Core;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using CareAgentTeamsBridge.Models;

namespace CareAgentTeamsBridge.Services;

/// <summary>
/// Calls the Azure AI Foundry hosted agent over its OpenAI-compatible Responses
/// endpoint, authenticating with the bridge's user-assigned managed identity
/// (audience https://ai.azure.com). The hosted agent stores responses
/// server-side, so follow-ups chain with `previous_response_id`.
/// </summary>
public sealed class FoundryAgentClient
{
    private static readonly string[] DataPlaneScopes = ["https://ai.azure.com/.default"];
    private static readonly JsonSerializerOptions JsonOptions = new(JsonSerializerDefaults.Web);

    private readonly HttpClient _httpClient;
    private readonly TokenCredential _credential;
    private readonly Uri _endpoint;
    private readonly ILogger<FoundryAgentClient> _logger;

    public FoundryAgentClient(HttpClient httpClient, IConfiguration configuration, ILogger<FoundryAgentClient> logger)
    {
        _httpClient = httpClient;
        _logger = logger;

        var endpoint = configuration["FOUNDRY_AGENT_RESPONSES_URL"]
            ?? throw new InvalidOperationException("FOUNDRY_AGENT_RESPONSES_URL is not configured.");
        _endpoint = new Uri(endpoint);
        if (_endpoint.Scheme != Uri.UriSchemeHttps ||
            !_endpoint.Host.EndsWith(".services.ai.azure.com", StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                "FOUNDRY_AGENT_RESPONSES_URL must be an HTTPS URL under *.services.ai.azure.com.");
        }

        var clientId = configuration["FOUNDRY_MI_CLIENT_ID"]
            ?? throw new InvalidOperationException("FOUNDRY_MI_CLIENT_ID is not configured.");
        _credential = new DefaultAzureCredential(new DefaultAzureCredentialOptions
        {
            ManagedIdentityClientId = clientId
        });
    }

    public async Task<CareResult> RespondAsync(
        string prompt,
        string? previousResponseId,
        CancellationToken cancellationToken)
    {
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(TimeSpan.FromMinutes(5));

        var result = await SendAsync(prompt, previousResponseId, timeout.Token);

        // A stale/expired previous_response_id must not brick the conversation:
        // retry once without chaining before giving up.
        if (result is null && !string.IsNullOrEmpty(previousResponseId))
        {
            _logger.LogWarning("Retrying Foundry call without previous_response_id.");
            result = await SendAsync(prompt, null, timeout.Token);
        }

        return result ?? throw new InvalidOperationException("The Foundry agent returned no usable response.");
    }

    private async Task<CareResult?> SendAsync(
        string prompt,
        string? previousResponseId,
        CancellationToken cancellationToken)
    {
        var payload = new Dictionary<string, object?>
        {
            ["input"] = prompt,
            ["stream"] = false,
        };
        if (!string.IsNullOrEmpty(previousResponseId))
        {
            payload["previous_response_id"] = previousResponseId;
        }

        var token = await _credential.GetTokenAsync(new TokenRequestContext(DataPlaneScopes), cancellationToken);
        using var request = new HttpRequestMessage(HttpMethod.Post, _endpoint)
        {
            Content = new StringContent(JsonSerializer.Serialize(payload, JsonOptions), Encoding.UTF8, "application/json")
        };
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token.Token);

        using var response = await _httpClient.SendAsync(request, cancellationToken);
        var body = await response.Content.ReadAsStringAsync(cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            _logger.LogError(
                "Foundry agent call failed with {StatusCode}: {Body}",
                (int)response.StatusCode,
                body.Length > 500 ? body[..500] : body);
            // 4xx with a chained id is likely a stale chain — signal a retry.
            if ((int)response.StatusCode is >= 400 and < 500 && !string.IsNullOrEmpty(previousResponseId))
            {
                return null;
            }
            throw new HttpRequestException($"Foundry agent returned HTTP {(int)response.StatusCode}.");
        }

        using var document = JsonDocument.Parse(body);
        var root = document.RootElement;

        var status = root.TryGetProperty("status", out var statusElement) ? statusElement.GetString() : null;
        if (string.Equals(status, "failed", StringComparison.OrdinalIgnoreCase))
        {
            var error = root.TryGetProperty("error", out var errorElement) ? errorElement.ToString() : "unknown error";
            throw new InvalidOperationException($"Foundry agent run failed: {error}");
        }

        var responseId =
            (root.TryGetProperty("response_id", out var responseIdElement) ? responseIdElement.GetString() : null)
            ?? (root.TryGetProperty("id", out var idElement) ? idElement.GetString() : null);

        var texts = new List<string>();
        if (root.TryGetProperty("output", out var output) && output.ValueKind == JsonValueKind.Array)
        {
            foreach (var item in output.EnumerateArray())
            {
                if (!item.TryGetProperty("content", out var content) || content.ValueKind != JsonValueKind.Array)
                {
                    continue;
                }

                foreach (var chunk in content.EnumerateArray())
                {
                    if (chunk.TryGetProperty("text", out var textElement))
                    {
                        var text = textElement.GetString();
                        if (!string.IsNullOrWhiteSpace(text))
                        {
                            texts.Add(text.Trim());
                        }
                    }
                }
            }
        }

        if (texts.Count == 0)
        {
            throw new InvalidOperationException("The Foundry agent response contained no text output.");
        }

        return new CareResult(responseId, string.Join("\n\n", texts));
    }
}
