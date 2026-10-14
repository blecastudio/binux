using System.Text.Json;
using Microsoft.Web.WebView2.WinForms;
using Microsoft.Web.WebView2.Core;

namespace Binux;
public sealed class TerminalForm : Form
{
    private readonly TabControl tabs=new() { Dock=DockStyle.Fill };
    private readonly ComboBox runtime=new() { DropDownStyle=ComboBoxStyle.DropDownList, Width=200 };
    private readonly List<ConPty> sessions=[];
    private readonly string data=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"BlecaStudio","binux");
    private bool closing;
    private AppSettings settings=AppSettings.Load();
    private readonly List<WebView2> terminals=[];
    public TerminalForm()
    {
        Text="binux 0.1.0 — BlecaStudio"; Width=1100; Height=720;
        foreach(string name in new[]{"home","rootfs","packages","addons","desktop","projects","logs","repos","cache","wbs","config"}) Directory.CreateDirectory(Path.Combine(data,name));
        var bar=new FlowLayoutPanel { Dock=DockStyle.Top,Height=40,WrapContents=false,AutoScroll=true };
        runtime.Items.AddRange(["Windows PowerShell","Linux / WSL (default distro)"]);
        runtime.SelectedIndex=0; bar.Controls.Add(runtime);
        void AddButton(string label,Action action) { var b=new Button {Text=label,AutoSize=true}; b.Click+=(_,_)=>action();bar.Controls.Add(b); }
        AddButton("+ Tab",()=>NewTab()); AddButton("Split",()=>Split()); AddButton("Stop / Close",()=>CloseTab());
        var language=new ComboBox {DropDownStyle=ComboBoxStyle.DropDownList,Width=100};language.Items.AddRange(["한국어","English"]);language.SelectedIndex=settings.Language=="ko"?0:1;
        language.SelectedIndexChanged+=(_,_)=>{settings=settings with {Language=language.SelectedIndex==0?"ko":"en"};settings.Save();Text=settings.Language=="ko"?"비눅스 0.1.0 — BlecaStudio":"binux 0.1.0 — BlecaStudio";};bar.Controls.Add(language);
        void ApplySettings(){settings.Save();foreach(var terminal in terminals.ToArray())Post(terminal,new {type="settings",font=settings.Font,theme=settings.Theme});}
        AddButton("A+",()=>{settings=settings with {Font=Math.Min(32,settings.Font+1)};ApplySettings();});
        AddButton("A−",()=>{settings=settings with {Font=Math.Max(9,settings.Font-1)};ApplySettings();});
        AddButton("Theme",()=>{settings=settings with {Theme=settings.Theme=="dark"?"light":"dark"};ApplySettings();});
        var searchBox=new TextBox {Width=120};bar.Controls.Add(searchBox);AddButton("Find / 검색",()=>{foreach(var terminal in terminals.Where(v=>!v.IsDisposed && tabs.SelectedTab!=null && tabs.SelectedTab.Contains(v)))Post(terminal,new {type="search",data=searchBox.Text});});
        Controls.Add(tabs); Controls.Add(bar);
        Shown+=(_,_)=>NewTab();
        FormClosing+=(_,_)=>{closing=true;foreach(var session in sessions.ToArray())session.Dispose();};
    }
    private async void NewTab()
    {
        var page=new TabPage(runtime.SelectedIndex==0?"PowerShell":"WSL Linux");
        tabs.TabPages.Add(page); tabs.SelectedTab=page;
        await CreatePane(page);
    }
    private async void Split()
    {
        if(tabs.SelectedTab is not {} page)return;
        var existing=page.Controls[0];page.Controls.Clear();
        var split=new SplitContainer {Dock=DockStyle.Fill,Orientation=Orientation.Vertical};
        split.Panel1.Controls.Add(existing);page.Controls.Add(split);split.SplitterDistance=Math.Max(100,page.Width/2);
        await CreatePane(split.Panel2);
    }
    private async Task CreatePane(Control parent)
    {
        int selection=runtime.SelectedIndex;
        var web=new WebView2 {Dock=DockStyle.Fill};parent.Controls.Add(web);terminals.Add(web);
        var pty=new ConPty();sessions.Add(pty);web.Tag=pty;
        try
        {
            var env=await CoreWebView2Environment.CreateAsync(userDataFolder:Path.Combine(data,"cache","webview"));
            await web.EnsureCoreWebView2Async(env);
            web.CoreWebView2.Settings.AreDevToolsEnabled=false;
            web.CoreWebView2.Settings.AreDefaultContextMenusEnabled=false;
            web.CoreWebView2.SetVirtualHostNameToFolderMapping("binux.local",Path.Combine(AppContext.BaseDirectory,"assets"),CoreWebView2HostResourceAccessKind.DenyCors);
            web.CoreWebView2.NavigationStarting+=(_,e)=>{if(!e.Uri.StartsWith("https://binux.local/",StringComparison.Ordinal))e.Cancel=true;};
            web.CoreWebView2.NewWindowRequested+=(_,e)=>e.Handled=true;
            pty.Output+=bytes=>Post(web,new {type="output",data=Convert.ToBase64String(bytes)});
            pty.Exited+=code=>Post(web,new {type="exit",code});
            web.CoreWebView2.WebMessageReceived+=(_,e)=>
            {
                try
                {
                    // Only our bundled local origin may control the PTY.
                    if(!e.Source.StartsWith("https://binux.local/",StringComparison.Ordinal))return;
                    using var json=JsonDocument.Parse(e.WebMessageAsJson);var root=json.RootElement;
                    switch(root.GetProperty("type").GetString())
                    {
                        case "ready":
                            Post(web,new {type="settings",font=settings.Font,theme=settings.Theme});
                            string command=selection==0?"powershell.exe -NoLogo":"wsl.exe --exec /bin/bash -i";
                            pty.Start(command,Path.Combine(data,"home"));
                            Post(web,new {type="banner",data="binux 0.1.0 / BlecaStudio\r\nRuntime: "+(selection==0?"Windows native PowerShell":"Linux / WSL")+"\r\nDesktop: optional\r\n"});
                            break;
                        case "input": pty.Write(root.GetProperty("data").GetString() ?? "");break;
                        case "resize": pty.Resize((short)Math.Clamp(root.GetProperty("cols").GetInt32(),2,500),(short)Math.Clamp(root.GetProperty("rows").GetInt32(),2,200));break;
                    }
                }
                catch(Exception error) {Post(web,new {type="error",data=error.Message});}
            };
            web.CoreWebView2.Navigate("https://binux.local/terminal.html");
        }
        catch(Exception error) {MessageBox.Show(this,"Terminal startup failed: "+error.Message,"binux");pty.Dispose();}
    }
    private void Post(WebView2 web,object message)
    {
        if(closing || web.IsDisposed || !IsHandleCreated)return;
        try { BeginInvoke(()=>{if(!web.IsDisposed && web.CoreWebView2!=null)web.CoreWebView2.PostWebMessageAsJson(JsonSerializer.Serialize(message));}); }
        catch(InvalidOperationException) {}
    }
    private void CloseTab()
    {
        if(tabs.SelectedTab is not {} page)return;
        void Stop(Control c) { if(c is WebView2 web && c.Tag is ConPty p) {p.Dispose();sessions.Remove(p);terminals.Remove(web);} foreach(Control child in c.Controls)Stop(child); }
        Stop(page);tabs.TabPages.Remove(page);page.Dispose();
    }
}
