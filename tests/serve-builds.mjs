import http from 'node:http';
import path from 'node:path';
import { readFile, stat } from 'node:fs/promises';

const types = { '.html':'text/html; charset=utf-8', '.js':'text/javascript', '.css':'text/css', '.pdf':'application/pdf', '.woff2':'font/woff2', '.ttf':'font/ttf', '.svg':'image/svg+xml', '.txt':'text/plain' };
const base = '/IGCSE0478-Checklist/';

// Test-only static servers emulate Pages: no SPA fallback for missing routes.
for (const [port, directory] of [[4322, '.preview-dist'], [4323, 'dist']]) {
  const root = path.resolve(directory);
  http.createServer(async (request, response) => {
    try {
      const url = new URL(request.url, 'http://127.0.0.1');
      if (!url.pathname.startsWith(base)) throw new Error('missing base');
      const relative = decodeURIComponent(url.pathname.slice(base.length));
      let file = path.resolve(root, relative);
      if (!file.startsWith(root + path.sep) && file !== root) throw new Error('outside build');
      if ((await stat(file)).isDirectory()) file = path.join(file, 'index.html');
      const body = await readFile(file);
      response.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
      response.end(body);
    } catch {
      response.writeHead(404, { 'Content-Type': 'text/html; charset=utf-8' });
      response.end(await readFile(path.join(root, '404.html')));
    }
  }).listen(port, '127.0.0.1', () => console.log(`Test build: http://127.0.0.1:${port}${base}`));
}
