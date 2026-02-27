require('dotenv').config();
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;

// Variables de entorno que se expondrán al frontend
const PUBLIC_ENV_KEYS = [
  'GROQ_API_KEY',
];

const server = http.createServer((req, res) => {
  // CORS para que el index.html pueda hacer fetch
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // Endpoint: GET /env → devuelve las keys como JSON
  if (req.method === 'GET' && req.url === '/env') {
    const env = {};
    for (const key of PUBLIC_ENV_KEYS) {
      env[key] = process.env[key] || '';
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(env));
    return;
  }

  // Endpoint: GET / → sirve el index.html del proyecto
  if (req.method === 'GET' && (req.url === '/' || req.url === '/index.html')) {
    const indexPath = path.join(__dirname, 'index.html');
    if (fs.existsSync(indexPath)) {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(fs.readFileSync(indexPath));
    } else {
      res.writeHead(404);
      res.end('index.html no encontrado');
    }
    return;
  }

  // Servir archivos estáticos del directorio raíz del proyecto
  const filePath = path.join(__dirname, req.url);
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath);
    const mime = {
      '.html': 'text/html',
      '.js': 'text/javascript',
      '.css': 'text/css',
      '.csv': 'text/csv',
      '.json': 'application/json',
      '.png': 'image/png',
      '.jpg': 'image/jpeg',
    }[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': mime });
    res.end(fs.readFileSync(filePath));
    return;
  }

  res.writeHead(404);
  res.end('Not found');
});

server.listen(PORT, () => {
  console.log(`\n✓ Servidor corriendo en http://localhost:${PORT}`);
  console.log(`✓ API keys disponibles en http://localhost:${PORT}/env`);
  console.log(`✓ App en http://localhost:${PORT}/\n`);
});
