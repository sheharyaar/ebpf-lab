// Minimal Chrome DevTools driver: open a file, wait for data-paged="done", save a screenshot and a PDF.
// usage: [CDP_PORT=9341 CDP_PROFILE=/tmp/cdp/p41] node render.mjs <file.html> <out-prefix> [screenshotHeight]
import { spawn } from 'node:child_process';
import { writeFileSync } from 'node:fs';
const [file, out, shotH = '3400'] = process.argv.slice(2);
const port = +(process.env.CDP_PORT || 9333);
const chrome = spawn('google-chrome-stable', ['--headless=new', '--disable-gpu', `--remote-debugging-port=${port}`,
  `--user-data-dir=${process.env.CDP_PROFILE || '/tmp/cdp/profile'}`, '--window-size=1000,1400', 'about:blank'], { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let target;
for (let i = 0; i < 50 && !target; i++) {
  await sleep(200);
  try { target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json(); } catch {}
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r));
let id = 0; const pending = new Map(); const logs = [];
ws.addEventListener('message', ev => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === 'Runtime.exceptionThrown') logs.push('EXC ' + JSON.stringify(m.params.exceptionDetails).slice(0, 300));
  if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') logs.push('ERR ' + JSON.stringify(m.params.args).slice(0, 300));
});
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
await send('Page.enable'); await send('Runtime.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1000, height: 1400, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url: 'file://' + file });
let done = false; const t0 = Date.now();
while (Date.now() - t0 < 90000) {
  await sleep(500);
  const r = await send('Runtime.evaluate', { expression: 'document.documentElement.dataset.paged || ""', returnByValue: true });
  if (r.result?.result?.value === 'done') { done = true; break; }
}
const info = await send('Runtime.evaluate', { returnByValue: true, expression:
  'JSON.stringify({pages: document.querySelectorAll(".pagedjs_page").length, h: document.documentElement.scrollHeight})' });
console.log('done', done, 'after', Date.now() - t0, 'ms', info.result?.result?.value, logs.join(' | ') || 'no errors');
const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true,
  clip: { x: 0, y: 0, width: 1000, height: +shotH, scale: 0.55 } });
writeFileSync(out + '-screen.png', Buffer.from(shot.result.data, 'base64'));
const pdf = await send('Page.printToPDF', { printBackground: true, preferCSSPageSize: true, displayHeaderFooter: false,
  marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0 });
writeFileSync(out + '.pdf', Buffer.from(pdf.result.data, 'base64'));
ws.close(); chrome.kill();
