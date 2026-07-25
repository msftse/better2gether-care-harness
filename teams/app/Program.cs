using Microsoft.Azure.Functions.Worker;
using Microsoft.Bot.Builder;
using Microsoft.Bot.Builder.Integration.AspNet.Core;
using Microsoft.Bot.Connector.Authentication;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using CareAgentTeamsBridge.Bot;
using CareAgentTeamsBridge.Services;

var host = new HostBuilder()
    .ConfigureFunctionsWebApplication()
    .ConfigureServices(services =>
    {
        services.AddApplicationInsightsTelemetryWorkerService();
        services.ConfigureFunctionsApplicationInsights();
        services.AddHttpClient<FoundryAgentClient>();

        services.AddSingleton<BotFrameworkAuthentication, ConfigurationBotFrameworkAuthentication>();
        services.AddSingleton<CloudAdapter, AdapterWithErrorHandler>();
        services.AddSingleton<IBotFrameworkHttpAdapter>(provider => provider.GetRequiredService<CloudAdapter>());
        services.AddTransient<IBot, CareAgentBot>();

        services.AddSingleton<CareQueue>();
        services.AddSingleton<SessionMapStore>();
    })
    .Build();

host.Run();
