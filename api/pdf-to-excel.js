const PDFParser = require('../pdf-parser');
const Busboy = require('busboy');

module.exports = async function handler(req, res) {
  // Habilitar CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const bb = Busboy({ headers: req.headers });
    const pdfBuffers = [];
    let uploadedFiles = 0;

    return new Promise((resolve, reject) => {
      bb.on('file', (fieldname, file, info) => {
        const chunks = [];
        file.on('data', (data) => chunks.push(data));
        file.on('end', () => {
          uploadedFiles++;
          pdfBuffers.push({
            filename: info.filename,
            buffer: Buffer.concat(chunks),
          });
        });
      });

      bb.on('finish', async () => {
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

          res.status(200).json({
            results,
            message: 'PDFs procesados exitosamente'
          });
          resolve();
        } catch (error) {
          res.status(500).json({ error: error.message });
          reject(error);
        }
      });

      bb.on('error', (error) => {
        res.status(400).json({ error: error.message });
        reject(error);
      });

      req.pipe(bb);
    });
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
}
