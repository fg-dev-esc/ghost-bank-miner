const pdfParse = require('pdf-parse');
const ExcelJS = require('exceljs');
const fs = require('fs');
const path = require('path');

/**
 * Parseador inteligente de PDF a Excel
 * Extrae datos estructurados y los organiza en celdas
 */

class PDFParser {
  constructor() {
    this.workbook = new ExcelJS.Workbook();
  }

  /**
   * Parsea un PDF y extrae texto, tablas y datos
   */
  async parsePDF(pdfBuffer) {
    try {
      const data = await pdfParse(pdfBuffer);
      return {
        text: data.text || '',
        pages: data.numpages || 0,
        metadata: data.metadata || {},
      };
    } catch (error) {
      throw new Error(`Error al parsear PDF: ${error.message}`);
    }
  }

  /**
   * Extracts OP number from text (from Concepto field or anywhere)
   */
  extractOPNumber(text) {
    const match = text.match(/OP\s+(\d+)/i);
    return match ? match[1] : null;
  }

  /**
   * Extrae campos clave-valor del texto
   * Busca patrones como "Campo: Valor" o "Campo = Valor"
   */
  extractFields(text) {
    const fields = {};
    const lines = text.split('\n');

    for (const line of lines) {
      // Busca patrones: "Campo: Valor" o "Campo = Valor"
      const match = line.match(/^([^:\n=]+)[:\s=]\s*(.+)$/);
      if (match) {
        const key = match[1].trim();
        const value = match[2].trim();

        // Filtra líneas que parecen ser campos válidos
        if (key.length > 2 && key.length < 100 && value.length > 0) {
          fields[key] = value;
          
          // Si es el campo Concepto, extraer y validar OP number
          if (key === 'Concepto') {
            const opNumber = this.extractOPNumber(value);
            if (opNumber) {
              fields['OP_Number'] = opNumber;
            }
          }
        }
      }
    }

    return fields;
  }

  /**
   * Extrae tablas del texto (busca filas con múltiples espacios)
   */
  extractTables(text) {
    const tables = [];
    const lines = text.split('\n');
    let currentTable = [];

    for (const line of lines) {
      const trimmed = line.trim();

      // Si la línea tiene contenido y múltiples espacios, es probablemente una fila
      if (trimmed && /\s{2,}/.test(line)) {
        const cells = trimmed.split(/\s{2,}/);
        currentTable.push(cells);
      } else if (trimmed === '' && currentTable.length > 0) {
        // Final de tabla
        if (currentTable.length > 1) {
          tables.push(currentTable);
        }
        currentTable = [];
      }
    }

    if (currentTable.length > 1) {
      tables.push(currentTable);
    }

    return tables;
  }

  /**
   * Crea un Excel con los datos extraídos
   */
  async createExcel(pdfData, outputPath) {
    const ws = this.workbook.addWorksheet('Datos Extraídos');

    // Estilo de encabezado
    const headerStyle = {
      font: { bold: true, color: { argb: 'FFFFFFFF' } },
      fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF4472C4' } },
      alignment: { horizontal: 'center', vertical: 'center' },
      border: {
        top: { style: 'thin' },
        left: { style: 'thin' },
        bottom: { style: 'thin' },
        right: { style: 'thin' },
      },
    };

    const cellStyle = {
      alignment: { vertical: 'top', wrapText: true },
      border: {
        top: { style: 'thin' },
        left: { style: 'thin' },
        bottom: { style: 'thin' },
        right: { style: 'thin' },
      },
    };

    let rowIndex = 1;

    // Agregar información del documento
    ws.getCell('A1').value = 'INFORMACIÓN DEL DOCUMENTO';
    ws.getCell('A1').style = headerStyle;
    ws.mergeCells('A1:B1');

    rowIndex = 2;
    ws.getCell(`A${rowIndex}`).value = 'Páginas';
    ws.getCell(`B${rowIndex}`).value = pdfData.pages;
    rowIndex++;

    if (pdfData.metadata.Title) {
      ws.getCell(`A${rowIndex}`).value = 'Título';
      ws.getCell(`B${rowIndex}`).value = pdfData.metadata.Title;
      rowIndex++;
    }

    // Agregar campos extraídos
    const fields = this.extractFields(pdfData.text);

    if (Object.keys(fields).length > 0) {
      rowIndex++;
      ws.getCell(`A${rowIndex}`).value = 'CAMPOS EXTRAÍDOS';
      ws.getCell(`A${rowIndex}`).style = headerStyle;
      ws.mergeCells(`A${rowIndex}:B${rowIndex}`);
      rowIndex++;

      for (const [key, value] of Object.entries(fields)) {
        ws.getCell(`A${rowIndex}`).value = key;
        ws.getCell(`A${rowIndex}`).style = {
          ...cellStyle,
          fill: { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFEBF1FF' } },
          font: { bold: true },
        };

        ws.getCell(`B${rowIndex}`).value = value;
        ws.getCell(`B${rowIndex}`).style = cellStyle;

        rowIndex++;
      }
    }

    // Agregar tablas encontradas
    const tables = this.extractTables(pdfData.text);

    for (let tableIdx = 0; tableIdx < tables.length; tableIdx++) {
      const table = tables[tableIdx];

      rowIndex++;
      ws.getCell(`A${rowIndex}`).value = `TABLA ${tableIdx + 1}`;
      ws.getCell(`A${rowIndex}`).style = headerStyle;
      ws.mergeCells(`A${rowIndex}:${String.fromCharCode(65 + table[0].length - 1)}${rowIndex}`);
      rowIndex++;

      // Agregar filas de la tabla
      for (const row of table) {
        for (let colIdx = 0; colIdx < row.length; colIdx++) {
          const cell = ws.getCell(`${String.fromCharCode(65 + colIdx)}${rowIndex}`);
          cell.value = row[colIdx];
          cell.style = cellStyle;
        }
        rowIndex++;
      }
    }

    // Agregar todo el texto
    if (pdfData.text) {
      rowIndex++;
      ws.getCell(`A${rowIndex}`).value = 'TEXTO COMPLETO';
      ws.getCell(`A${rowIndex}`).style = headerStyle;
      ws.mergeCells(`A${rowIndex}:B${rowIndex}`);
      rowIndex++;

      ws.getCell(`A${rowIndex}`).value = pdfData.text;
      ws.getCell(`A${rowIndex}`).style = {
        ...cellStyle,
        alignment: { vertical: 'top', wrapText: true },
      };
      ws.mergeCells(`A${rowIndex}:B${rowIndex}`);
      rowIndex++;
    }

    // Ajustar ancho de columnas
    ws.columns = [
      { width: 30 },
      { width: 50 },
    ];

    // Guardar archivo
    await this.workbook.xlsx.writeFile(outputPath);
    return outputPath;
  }

  /**
   * Procesa un PDF y lo convierte a Excel en un paso
   */
  async processFile(pdfBuffer, outputPath) {
    const pdfData = await this.parsePDF(pdfBuffer);
    return this.createExcel(pdfData, outputPath);
  }
}

module.exports = PDFParser;
