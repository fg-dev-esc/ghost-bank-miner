const PDFParser = require('./pdf-parser');
const fs = require('fs');
const path = require('path');

/**
 * Script de prueba para verificar que el parser funciona
 * Uso: node test-pdf-parser.js <ruta-pdf>
 */

async function test() {
  const pdfPath = process.argv[2];

  if (!pdfPath) {
    console.log('Uso: node test-pdf-parser.js <ruta-pdf>');
    console.log('Ejemplo: node test-pdf-parser.js ./documento.pdf');
    process.exit(1);
  }

  if (!fs.existsSync(pdfPath)) {
    console.error(`Error: Archivo no encontrado: ${pdfPath}`);
    process.exit(1);
  }

  try {
    console.log(`\n📄 Procesando: ${pdfPath}\n`);

    const pdfBuffer = fs.readFileSync(pdfPath);
    const parser = new PDFParser();
    const outputPath = path.join(
      __dirname,
      'test-output',
      path.parse(pdfPath).name + '.xlsx'
    );

    // Crear directorio de salida
    if (!fs.existsSync(path.join(__dirname, 'test-output'))) {
      fs.mkdirSync(path.join(__dirname, 'test-output'), { recursive: true });
    }

    await parser.processFile(pdfBuffer, outputPath);
    console.log(`✅ Excel generado: ${outputPath}`);
    console.log(`\n💡 Tip: Abre el archivo en Excel para ver los datos extraídos\n`);
  } catch (error) {
    console.error(`❌ Error: ${error.message}`);
    process.exit(1);
  }
}

test();
