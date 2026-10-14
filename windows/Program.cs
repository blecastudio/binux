namespace Binux;
internal static class Program
{
    [STAThread]
    static void Main(string[] args)
    {
        if(args.Length>0){Environment.ExitCode=NativeCli.Run(args);return;}
        Environment.SetEnvironmentVariable("PATH",AppContext.BaseDirectory+";"+Environment.GetEnvironmentVariable("PATH"));
        ApplicationConfiguration.Initialize();
        Application.Run(new TerminalForm());
    }
}
