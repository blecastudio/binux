using System.Text.Json;
namespace Binux;
public sealed record AppSettings(string Language="ko",int Font=15,string Theme="dark")
{
    public static string Root=>Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"BlecaStudio","binux");
    private static string FileName=>Path.Combine(Root,"config","settings.json");
    public static AppSettings Load() { try {return JsonSerializer.Deserialize<AppSettings>(File.ReadAllText(FileName)) ?? new();} catch(IOException){return new();} catch(JsonException){return new();} }
    public void Save() { Directory.CreateDirectory(Path.GetDirectoryName(FileName)!);string temp=FileName+"."+Guid.NewGuid().ToString("N")+".tmp";File.WriteAllText(temp,JsonSerializer.Serialize(this));File.Move(temp,FileName,true); }
}
