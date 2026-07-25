using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Bot.Builder;
using Microsoft.Bot.Builder.Integration.AspNet.Core;

namespace CareAgentTeamsBridge.Functions;

public sealed class MessagesFunction(IBotFrameworkHttpAdapter adapter, IBot bot)
{
    [Function("Messages")]
    public async Task<IActionResult> Run(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "messages")] HttpRequest request)
    {
        await adapter.ProcessAsync(request, request.HttpContext.Response, bot);
        return new EmptyResult();
    }
}
