'use strict';
const term = new Terminal({cursorBlink:true, fontFamily:'Cascadia Mono, Consolas, monospace',fontSize:15,scrollback:5000, theme:{background:'#14161b'}});
const fit = new FitAddon.FitAddon(); term.loadAddon(fit); term.open(document.getElementById('terminal'));
const search = new SearchAddon.SearchAddon();term.loadAddon(search);
const send = (type, rest={})=>chrome.webview.postMessage({type,...rest});
term.onData(data=>send('input',{data}));
term.onResize(({cols,rows})=>send('resize',{cols,rows}));
chrome.webview.addEventListener('message', ({data:m})=>{
 if(m.type==='output')term.write(Uint8Array.from(atob(m.data),c=>c.charCodeAt(0)));
 else if(m.type==='banner')term.write(m.data);
 else if(m.type==='exit')term.write(`\r\n[Process exited: ${m.code}]\r\n`);
 else if(m.type==='error')term.write(`\r\n[Error: ${m.data}]\r\n`);
 else if(m.type==='search')search.findNext(m.data);
 else if(m.type==='settings'){term.options.fontSize=m.font;term.options.theme={background:m.theme==='light'?'#ffffff':'#14161b',foreground:m.theme==='light'?'#14161b':'#ffffff'};fit.fit();}
});
new ResizeObserver(()=>fit.fit()).observe(document.getElementById('terminal'));
term.attachCustomKeyEventHandler(e=>{
 if(e.type==='keydown'&&e.ctrlKey&&e.shiftKey&&e.code==='KeyC'){navigator.clipboard.writeText(term.getSelection());return false;}
 if(e.type==='keydown'&&e.ctrlKey&&e.shiftKey&&e.code==='KeyV'){navigator.clipboard.readText().then(t=>term.paste(t));return false;}
 return true;
});
send('ready');fit.fit();term.focus();
