using Microsoft.Bot.Builder.Integration.AspNet.Core;
using Microsoft.Bot.Connector.Authentication;
using Microsoft.Extensions.Logging;

namespace CareAgentTeamsBridge.Bot;

public sealed class AdapterWithErrorHandler : CloudAdapter
{
    public AdapterWithErrorHandler(
        BotFrameworkAuthentication authentication,
        ILogger<IBotFrameworkHttpAdapter> logger)
        : base(authentication, logger)
    {
        OnTurnError = async (turnContext, exception) =>
        {
            logger.LogError(exception, "Unhandled bot turn error");
            await turnContext.SendActivityAsync(
                "I couldn't reach the care agent. Please try again or check Application Insights.");
        };
    }
}
