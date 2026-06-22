require('dotenv').config();
const http = require('http');
const fs = require('fs');
const path = require('path');
const PDFParser = require('./pdf-parser');

const PORT = 3000;

// Variables de entorno que se expondrán al frontend
const PUBLIC_ENV_KEYS = [
  'GROQ_API_KEY',
  'OPENROUTER_API_KEY',
  'GOOGLE_API_KEY',
  'MISTRAL_API_KEY',
  'SAMBANOVA_API_KEY',
  'COHERE_API_KEY',
  'CEREBRAS_API_KEY',
];

const server = http.createServer((req, res) => {
  // CORS para que el index.html pueda hacer fetch
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  // Endpoint: GET /env → devuelve las keys como JSON
  if (req.method === 'GET' && (req.url === '/env' || req.url === '/api/env')) {
    const env = {};
    for (const key of PUBLIC_ENV_KEYS) {
      env[key] = process.env[key] || '';
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(env));
    return;
  }

  // Endpoint: POST /api/chat → proxy para LLM providers (evita CORS)
  if (req.method === 'POST' && req.url === '/api/chat') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      try {
        const { url, key, payload } = JSON.parse(body);
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${key}`,
          },
          body: JSON.stringify(payload),
        });
        const data = await response.text();
        res.writeHead(response.status, { 'Content-Type': 'application/json' });
        res.end(data);
      } catch (error) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
      }
    });
    return;
  }

  // Endpoint: POST /api/pdf-to-excel → parsea PDF y retorna datos
  if (req.method === 'POST' && req.url === '/api/pdf-to-excel') {
    const busboy = require('busboy')({ headers: req.headers });
    const pdfBuffers = [];

    busboy.on('file', (fieldname, file, info) => {
      const chunks = [];
      file.on('data', (data) => chunks.push(data));
      file.on('end', () => {
        pdfBuffers.push({
          filename: info.filename,
          buffer: Buffer.concat(chunks),
        });
      });
    });

    busboy.on('finish', async () => {
      try {
        const results = [];
        for (const pdfFile of pdfBuffers) {
          const parser = new PDFParser();
          const pdfData = await parser.parsePDF(pdfFile.buffer);
          const fields = parser.extractFields(pdfData.text);
          const tables = parser.extractTables(pdfData.text);

          results.push({
            filename: pdfFile.filename,
            pages: pdfData.pages,
            metadata: pdfData.metadata,
            fields: fields,
            tables: tables,
            fullText: pdfData.text,
            success: true,
          });
        }

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ results, message: 'PDFs procesados exitosamente' }));
      } catch (error) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: error.message }));
      }
    });

    busboy.on('error', (error) => {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: error.message }));
    });

    req.pipe(busboy);
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
  console.log(`http://localhost:${PORT}/\n`);
});
