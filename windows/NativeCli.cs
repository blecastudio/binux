using System.Runtime.InteropServices;
namespace Binux;
internal static class NativeCli
{
    [DllImport("kernel32.dll")] private static extern bool AttachConsole(uint pid);
    public static int Run(string[] args)
    {
        AttachConsole(0xFFFFFFFF);
        var settings=AppSettings.Load();
        string help="binux help | version | info | doctor | lang list|show|set ko|en | storage info | settings list\nLinux management: install Python binux tools inside WSL. Native bg/addon/Desktop/WBS adapters are pending.";
        try
        {
            if(args.Contains("--help") || args[0] is "help" or "--help") {Console.WriteLine(help);return 0;}
            switch(args[0])
            {
                case "version":Console.WriteLine("binux 0.1.0");return 0;
                case "info":Console.WriteLine($"binux 0.1.0 / BlecaStudio\nRuntime: Windows native ConPTY / optional WSL\nData: {AppSettings.Root}\nDesktop: optional, not installed by this Windows app");return 0;
                case "doctor":Console.WriteLine($"Windows: {Environment.OSVersion}\nArchitecture: {RuntimeInformation.OSArchitecture}\nConPTY requires Windows 10 1809+\n.NET: {Environment.Version}\nWSL install is managed by Windows; check wsl --status\nWebView2 Runtime must be installed");return 0;
                case "lang":
                    if(args.Length>1 && args[1]=="list") {Console.WriteLine("ko: 한국어 / ko-KR\nen: English / en-US");return 0;}
                    if(args.Length==3 && args[1]=="set" && args[2] is "ko" or "en") {(settings with {Language=args[2]}).Save();Console.WriteLine(args[2]);return 0;}
                    if(args.Length==2 && args[1]=="show") {Console.WriteLine(settings.Language);return 0;}
                    throw new ArgumentException("binux lang list|show|set ko|en");
                case "settings":Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(settings));return 0;
                case "storage":
                    if(args.Length==2 && args[1]=="info") {Directory.CreateDirectory(AppSettings.Root);foreach(string folder in Directory.GetDirectories(AppSettings.Root)){long size=Directory.EnumerateFiles(folder,"*",SearchOption.AllDirectories).Sum(path=>new FileInfo(path).Length);Console.WriteLine($"{Path.GetFileName(folder)}: {size} bytes");}return 0;}
                    throw new ArgumentException("binux storage info");
                default:throw new NotSupportedException("Native Windows command adapter is unavailable. Use binux help and the Linux/WSL host tools.");
            }
        }
        catch(Exception error){Console.Error.WriteLine((settings.Language=="ko"?"오류: ":"Error: ")+error.Message);return 1;}
    }
}
