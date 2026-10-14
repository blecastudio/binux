using System.Runtime.InteropServices;
namespace Binux;
internal static class NativeCli
{
    [DllImport("kernel32.dll")] private static extern bool AttachConsole(uint pid);
    public static int Run(string[] args)
    {
        AttachConsole(0xFFFFFFFF);
        var settings=AppSettings.Load();
        string help="binux help | version | info | doctor | lang list|show|set ko|en | storage info | settings list\nLinux commands run in the selected WSL distribution: bg/server/addon/package/Desktop/WBS.\nbinux runtime list | install debian|ubuntu | use debian|ubuntu | tools | exec <command> [args...]";
        try
        {
            if(args[0] is "help" or "--help" || (args[0] is "version" or "info" or "doctor" or "lang" or "runtime" or "settings" or "storage" && args.Contains("--help"))) {Console.WriteLine(help);return 0;}
            switch(args[0])
            {
                case "version":Console.WriteLine("binux 1.0.0");return 0;
                case "info":Console.WriteLine($"binux 1.0.0 / BlecaStudio\nRuntime: Windows native ConPTY / optional WSL\nData: {AppSettings.Root}\nDesktop: optional, not installed by this Windows app");return 0;
                case "doctor":Console.WriteLine($"Windows: {Environment.OSVersion}\nArchitecture: {RuntimeInformation.OSArchitecture}\nConPTY requires Windows 10 1809+\n.NET: {Environment.Version}\nWSL install is managed by Windows; check wsl --status\nWebView2 Runtime must be installed");return 0;
                case "lang":
                    if(args.Length>1 && args[1]=="list") {Console.WriteLine("ko: 한국어 / ko-KR\nen: English / en-US");return 0;}
                    if(args.Length==3 && args[1]=="set" && args[2] is "ko" or "en") {(settings with {Language=args[2]}).Save();Console.WriteLine(args[2]);return 0;}
                    if(args.Length==2 && args[1]=="show") {Console.WriteLine(settings.Language);return 0;}
                    throw new ArgumentException("binux lang list|show|set ko|en");
                case "settings":
                    if(args.Length==4 && args[1]=="set" && args[3] is "on" or "off"){
                        settings=args[2] switch {"toolbar"=>settings with {Toolbar=args[3]=="on"},"fullscreen"=>settings with {Fullscreen=args[3]=="on"},_=>throw new ArgumentException("settings set toolbar|fullscreen on|off")};settings.Save();
                    }
                    Console.WriteLine(System.Text.Json.JsonSerializer.Serialize(settings));return 0;
                case "runtime":
                    if(args.Length==2 && args[1]=="list")return Wsl(["--list","--verbose"]);
                    if(args.Length==3 && args[1] is "use" or "install"){
                        string distro=args[2] switch {"debian"=>"Debian","ubuntu"=>"Ubuntu",_=>throw new ArgumentException("debian or ubuntu required")};
                        if(args[1]=="install")return Wsl(["--install","--distribution",distro,"--no-launch"]);
                        (settings with {WslDistro=distro}).Save();Console.WriteLine($"WSL distribution: {distro}");return 0;
                    }
                    if(args.Length==2 && args[1]=="tools")return Wsl(["--distribution",settings.WslDistro,"--exec","sudo","apt-get","install","-y","python3","python3-cryptography","python3-venv","python3-pip","nodejs","npm","git","openssh-client","curl"]);
                    if(args.Length>2 && args[1]=="exec")return Wsl(["--distribution",settings.WslDistro,"--exec",..args.Skip(2)]);
                    throw new ArgumentException(help);
                case "storage":
                    if(args.Length==2 && args[1]=="info") {Directory.CreateDirectory(AppSettings.Root);foreach(string folder in Directory.GetDirectories(AppSettings.Root)){long size=Directory.EnumerateFiles(folder,"*",SearchOption.AllDirectories).Sum(path=>new FileInfo(path).Length);Console.WriteLine($"{Path.GetFileName(folder)}: {size} bytes");}return 0;}
                    throw new ArgumentException("binux storage info");
                default:
                    string module=args[0]=="wbs"?"binux.wbs":"binux.cli";
                    string script="export BINUX_DEVICE_TARGET=windows; export PYTHONPATH=\"$(wslpath -u \"$1\")\"; shift; exec python3 -m \"$@\"";
                    return Wsl(["--distribution",settings.WslDistro,"--exec","/bin/bash","-c",script,"binux-wsl",Path.Combine(AppContext.BaseDirectory,"core"),module,..(args[0]=="wbs"?args.Skip(1):args)]);
            }
        }
        catch(Exception error){Console.Error.WriteLine((settings.Language=="ko"?"오류: ":"Error: ")+error.Message);return 1;}
    }
    private static int Wsl(string[] arguments){
        var info=new System.Diagnostics.ProcessStartInfo("wsl.exe"){UseShellExecute=false};
        foreach(string argument in arguments)info.ArgumentList.Add(argument);
        using var process=System.Diagnostics.Process.Start(info) ?? throw new IOException("Cannot start WSL");process.WaitForExit();return process.ExitCode;
    }
}
