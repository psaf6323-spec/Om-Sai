// Zero-dependency static server for Om Sai (Node 18+).  Usage: npm start  ->  http://localhost:8080
const http = require('http'), fs = require('fs'), path = require('path');
const PORT = Number(process.env.PORT) || 8080, HOST = process.env.HOST || '127.0.0.1';
const FILES = {
  '/': ['index.html', 'text/html; charset=utf-8'], '/index.html': ['index.html', 'text/html; charset=utf-8'],
  '/sw.js': ['sw.js', 'text/javascript; charset=utf-8'], '/manifest.webmanifest': ['manifest.webmanifest', 'application/manifest+json'],
  '/icons/icon-192.png': ['icons/icon-192.png', 'image/png'], '/icons/icon-512.png': ['icons/icon-512.png', 'image/png']
};
const HEADERS = {
  'Cache-Control': 'no-cache',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'no-referrer',
  'X-Frame-Options': 'SAMEORIGIN',
  'Permissions-Policy': 'camera=(self), microphone=(self), geolocation=()'
};
http.createServer((req, res) => {
  const url = (req.url || '/').split('?')[0];
  if (req.method !== 'GET' && req.method !== 'HEAD') { res.writeHead(405); return res.end(); }
  const f = FILES[url];
  if (!f) { res.writeHead(404, { 'Content-Type': 'text/plain' }); return res.end('Not found'); }
  fs.readFile(path.join(__dirname, f[0]), (err, buf) => {
    if (err) { res.writeHead(500); return res.end('Cannot read file'); }
    res.writeHead(200, { ...HEADERS, 'Content-Type': f[1] }); res.end(req.method === 'HEAD' ? undefined : buf);
  });
}).listen(PORT, HOST, () => console.log(`Om Sai running at http://${HOST === '0.0.0.0' ? 'localhost' : HOST}:${PORT}`));
