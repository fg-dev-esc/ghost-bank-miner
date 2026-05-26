import os, re, shutil, csv, hashlib
from pypdf import PdfReader, PdfWriter
from datetime import datetime

PATRONES = [
    {'nombre': 'OP REF', 'regex': r'op\s*(\d+)\s*ref'},
    {'nombre': 'OP SIMPLE', 'regex': r'op\s+(\d+)(?:\s|$)'},
    {'nombre': 'SANOFI', 'regex': r'sanofi\s*(\d+)\s*ref'}
]

# Patrón para detectar PDFs con formato distinto (Reporte de operaciones)
PATRON_REPORTE_OPERACIONES = r'Reporte de operaciones|Descarga masiva'

# ============================================================================
# FUNCIÓN PARA CALCULAR HASH DE ARCHIVO
# ============================================================================
def calcular_hash_archivo(filepath):
    """Calcula SHA256 hash de un archivo para detectar duplicados"""
    try:
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except:
        return None

# ============================================================================
# CONFIGURACIÓN - CARPETA A PROCESAR
# ============================================================================
import sys

# Determinar carpeta a procesar
if len(sys.argv) > 1:
    root_folder = os.path.abspath(sys.argv[1])
else:
    # Usar la carpeta por defecto
    root_folder = r'C:\Users\luis.fernandez\OneDrive - ESCOTEL ESPECIALISTAS EN CONTACTO TELEFONICO S.A. DE C.V\Archivos de Andrea José Ramírez - Desarrollo comprobantes 2'

# Validar que la carpeta existe
if not os.path.isdir(root_folder):
    print(f"ERROR: La carpeta no existe: {root_folder}")
    exit(1)

# CARPETA RAÍZ (donde se guardarán CSV y TXT) - donde está el script
script_folder = os.path.dirname(os.path.abspath(__file__))

print(f"Procesando recursivamente desde: {root_folder}\n")

resultados = []
id_counter = 1
archivos_procesados = {}  # Cambio a dict para hash
archivos_hash = {}
# CSV y TXT EN LA CARPETA DEL SCRIPT, NO EN LA CARPETA PROCESADA
csv_path = os.path.join(script_folder, 'resumen-de-extracción.csv')

# ============================================================================
# CARGAR CSV MAESTRO EXISTENTE (para idempotencia)
# ============================================================================
if os.path.exists(csv_path):
    try:
        with open(csv_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ruta_original = row.get('Ruta Original', '')
                hash_archivo = row.get('Hash Archivo', '')

                info_csv = {
                    'id': int(row['ID']) if row.get('ID') else id_counter,
                    'nombre_original': row.get('Nombre Original', ''),
                    'ruta_original': ruta_original,
                    'carpeta': row.get('Carpeta', ''),
                    'contexto': row.get('Contexto de Extracción', ''),
                    'nombre_nuevo': row.get('Nombre Nuevo', ''),
                    'estatus': row.get('Estatus', ''),
                    'hash': hash_archivo,
                    'validacion_clave': row.get('Clave de Rastreo', '')
                }

                # Indexar por ruta original
                if ruta_original:
                    archivos_procesados[ruta_original] = info_csv

                # Indexar por hash
                if hash_archivo:
                    archivos_hash[hash_archivo] = info_csv

                resultados.append(info_csv)

                if row.get('ID'):
                    try:
                        id_counter = max(id_counter, int(row['ID']) + 1)
                    except ValueError:
                        pass

        print(f"CSV MAESTRO CARGADO:")
        print(f"  ✓ Total registros: {len(resultados)}")
        print(f"  ✓ Archivos únicos por ruta: {len(archivos_procesados)}")
        print(f"  ✓ Archivos únicos por hash: {len(archivos_hash)}")
        print(f"  ✓ Continuando desde ID: {id_counter}\n")
    except Exception as e:
        print(f"⚠ No se pudo leer CSV: {e}")
        print("Se creará un nuevo CSV.\n")

error_files = []
masivos_omitidos = 0
hojas_sin_patron = 0
paginas_masivo_omitidas = 0
archivos_omitidos_por_csv = 0
archivos_omitidos_por_hash = 0
archivos_nuevos = 0

print("="*80)
print("INICIANDO ESCANEO DE ARCHIVOS PDF")
print("="*80 + "\n")

# ============================================================================
# PROCESAR CARPETAS RECURSIVAMENTE
# ============================================================================
for root, dirs, files in os.walk(root_folder):
    # SALTAR carpetas de salida
    if 'archivos-renombrados' in root or 'formato-distinto-al-esperado' in root:
        continue

    pdf_files = [f for f in files if f.endswith('.pdf')]

    if pdf_files:
        carpeta_relativa = os.path.relpath(root, root_folder)
        print(f"\n{'='*80}")
        print(f"📁 PROCESANDO: {carpeta_relativa}")
        print(f"{'='*80}")
        print(f"   Encontrados {len(pdf_files)} PDFs\n")

        # Crear carpeta de salida en la MISMA carpeta
        output_folder = os.path.join(root, 'archivos-renombrados')
        os.makedirs(output_folder, exist_ok=True)

        for f in pdf_files:
            path = os.path.join(root, f)

            # ========================================================================
            # VERIFICACIÓN 1: ¿Ya fue procesado según la ruta en el CSV?
            # ========================================================================
            if path in archivos_procesados:
                info_previa = archivos_procesados[path]
                print(f"   ⊘ [OMITIDO - CSV] Ya procesado: {f}")
                print(f"                    ID: {info_previa['id']}, Estatus: {info_previa['estatus']}")
                archivos_omitidos_por_csv += 1
                continue

            # ========================================================================
            # VERIFICACIÓN 2: ¿Es un duplicado por hash?
            # ========================================================================
            hash_actual = calcular_hash_archivo(path)
            if hash_actual and hash_actual in archivos_hash:
                info_previa = archivos_hash[hash_actual]
                print(f"   ⊘ [OMITIDO - DUPLICADO] Mismo contenido que:")
                print(f"                           {os.path.basename(info_previa['ruta_original'])}")
                print(f"                           ID: {info_previa['id']}")
                archivos_omitidos_por_hash += 1
                continue

            # ========================================================================
            # ARCHIVO NUEVO - Procesar
            # ========================================================================
            archivos_nuevos += 1

            resultado = {
                'id': id_counter,
                'nombre_original': f,
                'ruta_original': path,
                'carpeta': carpeta_relativa,
                'contexto': '',
                'nombre_nuevo': '',
                'estatus': '',
                'hash': hash_actual,
                'validacion_clave': ''
            }

            try:
                reader = PdfReader(path)
                text_primera_pagina = reader.pages[0].extract_text()

                # Verificar si el PDF es editable (contiene texto extractible)
                es_editable = text_primera_pagina and len(text_primera_pagina.strip()) > 0

                if not es_editable:
                    # OMITIR PDFs de imagen - no se procesan ni se guardan
                    hojas_sin_patron += 1
                    print(f"   ⊘ [{id_counter}] PDF NO EDITABLE (imagen): {f}")
                    resultado['estatus'] = 'PDF no editable (imagen)'
                    resultados.append(resultado)
                    id_counter += 1
                    continue

                # Detectar si es un PDF con formato distinto (Reporte de operaciones)
                es_formato_distinto = re.search(PATRON_REPORTE_OPERACIONES, text_primera_pagina, re.IGNORECASE)

                if es_formato_distinto:
                    # PDF MASIVO - Extraer cada página como PDF individual
                    print(f"   ★ [{id_counter}] PDF MASIVO: {f}")
                    print(f"       Total de páginas: {len(reader.pages)}")

                    paginas_procesadas = 0
                    paginas_omitidas = 0
                    paginas_formato_distinto = 0

                    # Crear carpeta para formato distinto
                    error_folder = os.path.join(root, 'formato-distinto-al-esperado')
                    os.makedirs(error_folder, exist_ok=True)

                    # Guardar ID del masivo para referencia
                    id_masivo = id_counter
                    id_counter += 1

                    for page_num in range(len(reader.pages)):
                        page_text = reader.pages[page_num].extract_text()

                        # Contar operaciones en esta página
                        op_matches = re.findall(r'OP\s*(\d+)', page_text, re.IGNORECASE)

                        # Si tiene más de 1 operación = LISTADO INFORMATIVO (omitir)
                        if len(op_matches) > 1:
                            paginas_omitidas += 1
                            continue

                        # Crear PDF con esta página
                        writer = PdfWriter()
                        writer.add_page(reader.pages[page_num])

                        # Si tiene exactamente 1 operación = COMPROBANTE INDIVIDUAL (procesar)
                        if len(op_matches) == 1:
                            op_numero = op_matches[0]
                            nuevo_nombre = f"{op_numero}.pdf"
                            new_path = os.path.join(output_folder, nuevo_nombre)

                            # Manejar duplicados
                            if os.path.exists(new_path):
                                base, ext = os.path.splitext(nuevo_nombre)
                                counter = 1
                                while os.path.exists(os.path.join(output_folder, f"{base}-{counter}{ext}")):
                                    counter += 1
                                nuevo_nombre = f"{base}-{counter}{ext}"
                                new_path = os.path.join(output_folder, nuevo_nombre)

                            with open(new_path, 'wb') as out_f:
                                writer.write(out_f)

                            # Agregar página extraída al CSV
                            resultado_pagina = {
                                'id': id_counter,
                                'nombre_original': f'{f} (pagina {page_num + 1})',
                                'ruta_original': path,
                                'carpeta': carpeta_relativa,
                                'contexto': f'Extraido de masivo ID {id_masivo}',
                                'nombre_nuevo': nuevo_nombre,
                                'estatus': 'Masivo - Exito',
                                'hash': hash_actual,
                                'validacion_clave': ''
                            }
                            resultados.append(resultado_pagina)
                            archivos_hash[hash_actual] = resultado_pagina
                            id_counter += 1
                            paginas_procesadas += 1

                        else:
                            # No tiene patrón OP = Formato distinto, extraer con nombre pagina_{num}
                            nuevo_nombre = f"pagina_{page_num}.pdf"
                            new_path = os.path.join(error_folder, nuevo_nombre)

                            # Manejar duplicados
                            if os.path.exists(new_path):
                                base, ext = os.path.splitext(nuevo_nombre)
                                counter = 1
                                while os.path.exists(os.path.join(error_folder, f"{base}-{counter}{ext}")):
                                    counter += 1
                                nuevo_nombre = f"{base}-{counter}{ext}"
                                new_path = os.path.join(error_folder, nuevo_nombre)

                            with open(new_path, 'wb') as out_f:
                                writer.write(out_f)

                            # Agregar página formato distinto al CSV
                            resultado_pagina = {
                                'id': id_counter,
                                'nombre_original': f'{f} (pagina {page_num + 1})',
                                'ruta_original': path,
                                'carpeta': carpeta_relativa,
                                'contexto': f'Extraido de masivo ID {id_masivo} - Sin patron OP',
                                'nombre_nuevo': nuevo_nombre,
                                'estatus': 'Formato distinto al esperado',
                                'hash': hash_actual,
                                'validacion_clave': ''
                            }
                            resultados.append(resultado_pagina)
                            archivos_hash[hash_actual] = resultado_pagina
                            id_counter += 1
                            paginas_formato_distinto += 1

                    paginas_masivo_omitidas += paginas_omitidas

                    # Agregar el archivo masivo completo al CSV como un único registro
                    resultado['id'] = id_masivo
                    resultado['contexto'] = f'PDF Masivo - {len(reader.pages)} paginas totales'
                    resultado['nombre_nuevo'] = f'{paginas_procesadas} renombradas, {paginas_formato_distinto} formato distinto, {paginas_omitidas} omitidas'
                    resultado['estatus'] = 'Masivo - Procesado'

                    print(f"       ✓ Paginas procesadas: {paginas_procesadas}")
                    print(f"       ⚠ Paginas formato distinto: {paginas_formato_distinto}")
                    print(f"       ⊘ Paginas omitidas: {paginas_omitidas}")

                    resultados.append(resultado)
                    archivos_procesados[path] = resultado
                    if hash_actual:
                        archivos_hash[hash_actual] = resultado
                    continue

                else:
                    # Procesamiento normal para formato estándar
                    match = None
                    for patron in PATRONES:
                        match = re.search(patron['regex'], text_primera_pagina, re.IGNORECASE)
                        if match:
                            break

                    if match:
                        start = max(0, match.start() - 50)
                        end = min(len(text_primera_pagina), match.end() + 50)
                        contexto = text_primera_pagina[start:end].replace('\n', ' ').strip()

                        nuevo_nombre = f"{match.group(1)}.pdf"
                        new_path = os.path.join(output_folder, nuevo_nombre)

                        if os.path.exists(new_path):
                            base, ext = os.path.splitext(nuevo_nombre)
                            counter = 1
                            while os.path.exists(os.path.join(output_folder, f"{base}-{counter}{ext}")):
                                counter += 1
                            nuevo_nombre = f"{base}-{counter}{ext}"
                            new_path = os.path.join(output_folder, nuevo_nombre)

                        shutil.copy(path, new_path)

                        resultado['contexto'] = contexto
                        resultado['nombre_nuevo'] = nuevo_nombre
                        resultado['estatus'] = 'Éxito'

                        print(f"   ✓ [{id_counter}] {f} → {nuevo_nombre}")
                    else:
                        resultado['estatus'] = 'No se encontró patrón'
                        print(f"   ⚠ [{id_counter}] No se encontró patrón: {f}")
                        error_files.append((path, f, root))

            except Exception as e:
                resultado['estatus'] = f'Error: {str(e)}'
                print(f"   ✗ [{id_counter}] Error en {f}: {e}")
                error_files.append((path, f, root))

            resultados.append(resultado)
            archivos_procesados[path] = resultado
            if hash_actual:
                archivos_hash[hash_actual] = resultado
            id_counter += 1

print("\n" + "="*80)
print("RESUMEN DE ESCANEO")
print("="*80)
print(f"Archivos nuevos detectados: {archivos_nuevos}")
print(f"Archivos omitidos (ya en CSV): {archivos_omitidos_por_csv}")
print(f"Archivos omitidos (duplicado por hash): {archivos_omitidos_por_hash}")
print(f"Total archivos analizados: {archivos_nuevos + archivos_omitidos_por_csv + archivos_omitidos_por_hash}\n")

# ============================================================================
# FUNCIÓN PARA EXTRAER CLAVE DE RASTREO (antes de escribir CSV)
# ============================================================================
PATRON_CLAVE_RASTREO = r'Clave\s*de\s*Rastreo[:\s]+(\d+[A-Z0-9]+)'

def extraer_clave_rastreo(pdf_path):
    """Extrae la clave de rastreo de todas las páginas del PDF"""
    try:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                match = re.search(PATRON_CLAVE_RASTREO, text, re.IGNORECASE)
                if match:
                    return match.group(1)
    except:
        pass
    return None

# ============================================================================
# VALIDAR DUPLICADOS Y AGREGAR COLUMNA AL CSV (SOLO NUEVOS)
# ============================================================================
print("\n" + "="*80)
print("Validando duplicados por clave de rastreo...")
print("="*80 + "\n")

archivos_validados_totales = 0
archivos_omitidos_validacion = 0

for r in resultados:
    nombre_nuevo = r.get('nombre_nuevo', '')
    validacion_actual = r.get('validacion_clave', '')

    # ========================================================================
    # SOLO VALIDAR SI NO FUE VALIDADO ANTES
    # ========================================================================
    # Si ya tiene validación del CSV anterior → NO REPETIR
    if validacion_actual and validacion_actual.strip():
        # Ya fue validado, omitir
        archivos_omitidos_validacion += 1
        continue

    # ========================================================================
    # VALIDAR NUEVOS DUPLICADOS
    # ========================================================================
    # Si tiene nombre nuevo y es potencial duplicado (sufijo -1, -2, etc.)
    match_dup = re.match(r'^(\d+)-(\d+)\.pdf$', nombre_nuevo)

    if match_dup:
        numero_op = match_dup.group(1)
        archivo_original = f"{numero_op}.pdf"

        # Buscar el archivo original en los resultados
        ruta_duplicado = None
        ruta_original_pdf = None

        # Encontrar la ruta del duplicado
        for root, dirs, files in os.walk(root_folder):
            if 'archivos-renombrados' in root and nombre_nuevo in files:
                ruta_duplicado = os.path.join(root, nombre_nuevo)
                ruta_original_pdf = os.path.join(root, archivo_original)
                break

        if ruta_duplicado and ruta_original_pdf and os.path.exists(ruta_original_pdf):
            clave_original = extraer_clave_rastreo(ruta_original_pdf)
            clave_duplicado = extraer_clave_rastreo(ruta_duplicado)

            if clave_original and clave_duplicado:
                if clave_original == clave_duplicado:
                    r['validacion_clave'] = 'Coincide'
                else:
                    r['validacion_clave'] = f'Error (Orig: {clave_original}, Dup: {clave_duplicado})'
            else:
                r['validacion_clave'] = 'Error al extraer'
        else:
            r['validacion_clave'] = 'Original no encontrado'

        archivos_validados_totales += 1
    else:
        # No es duplicado, dejar vacío
        r['validacion_clave'] = ''

print(f"Archivos validados (nuevos): {archivos_validados_totales}")
print(f"Archivos omitidos (ya validados): {archivos_omitidos_validacion}\n")

# ============================================================================
# ESCRIBIR CSV CONSOLIDADO EN LA CARPETA DEL SCRIPT (NO EN root_folder)
# ============================================================================
with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
    fieldnames = ['ID', 'Nombre Original', 'Ruta Original', 'Carpeta', 'Contexto de Extracción', 'Nombre Nuevo', 'Estatus', 'Clave de Rastreo', 'Hash Archivo']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)

    writer.writeheader()
    for r in resultados:
        writer.writerow({
            'ID': r['id'],
            'Nombre Original': r['nombre_original'],
            'Ruta Original': r['ruta_original'],
            'Carpeta': r.get('carpeta', ''),
            'Contexto de Extracción': r['contexto'],
            'Nombre Nuevo': r['nombre_nuevo'],
            'Estatus': r['estatus'],
            'Clave de Rastreo': r.get('validacion_clave', ''),
            'Hash Archivo': r.get('hash', '')
        })

# ============================================================================
# CONTAR Y GENERAR RESUMEN
# ============================================================================
pdfs_individuales = sum(1 for r in resultados if r.get('estatus') == 'Éxito')
pdfs_masivos_extraidos = sum(1 for r in resultados if r.get('estatus') == 'Masivo - Exito')
pdfs_formato_distinto_extraidos = sum(1 for r in resultados if r.get('estatus') == 'Formato distinto al esperado')
pdfs_no_encontro_patron = sum(1 for r in resultados if r.get('estatus') == 'No se encontró patrón')
pdfs_no_editables = sum(1 for r in resultados if r.get('estatus') == 'PDF no editable (imagen)')

# Total de comprobantes renombrados
comprobantes_renombrados = pdfs_individuales + pdfs_masivos_extraidos

# Total formato distinto
total_formato_distinto = pdfs_formato_distinto_extraidos + pdfs_no_encontro_patron

# Total de hojas omitidas
hojas_omitidas = paginas_masivo_omitidas + pdfs_no_editables

# Total de hojas procesadas
total_hojas = comprobantes_renombrados + total_formato_distinto + hojas_omitidas

# ============================================================================
# IMPRIMIR RESUMEN EN CONSOLA
# ============================================================================
print(f"\n{'='*80}")
print(f"RESUMEN FINAL - Procesamiento recursivo")
print(f"{'='*80}")
print(f"\nCOMPROBANTES RENOMBRADOS:")
print(f"  - PDFs individuales: {pdfs_individuales}")
print(f"  - Paginas extraidas de masivos: {pdfs_masivos_extraidos}")
print(f"  - Total comprobantes renombrados: {comprobantes_renombrados}")
print(f"\nFORMATO DISTINTO AL ESPERADO:")
print(f"  - Paginas extraidas de masivos (sin OP): {pdfs_formato_distinto_extraidos}")
print(f"  - PDFs individuales (sin patron): {pdfs_no_encontro_patron}")
print(f"  - Total formato distinto: {total_formato_distinto}")
print(f"\nHOJAS OMITIDAS:")
print(f"  - Paginas listado informativo (masivos): {paginas_masivo_omitidas}")
print(f"  - PDFs no editables (imagen): {pdfs_no_editables}")
print(f"  - Total hojas omitidas: {hojas_omitidas}")
print(f"\nTOTAL DE HOJAS EN ARCHIVOS: {total_hojas}")
print(f"\nVERIFICACION:")
print(f"  {comprobantes_renombrados} + {total_formato_distinto} + {hojas_omitidas} = {comprobantes_renombrados + total_formato_distinto + hojas_omitidas}")

if comprobantes_renombrados + total_formato_distinto + hojas_omitidas == total_hojas:
    print(f"  ✓ OK - VERIFICACION EXITOSA")
else:
    print(f"  ✗ ERROR - Las sumas no coinciden")

print(f"\n✓ CSV Consolidado: {csv_path}")

# ============================================================================
# GUARDAR RESUMEN EN TXT EN LA CARPETA DEL SCRIPT (NO EN root_folder)
# ============================================================================
txt_path = os.path.join(script_folder, 'resumen-procesamiento.txt')
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(txt_path, 'w', encoding='utf-8-sig') as txtfile:
    txtfile.write("="*80 + "\n")
    txtfile.write("RESUMEN CONSOLIDADO DE PROCESAMIENTO DE PDFs\n")
    txtfile.write("="*80 + "\n")
    txtfile.write(f"Fecha/Hora de ejecución: {timestamp}\n")
    txtfile.write(f"Ruta raíz procesada: {root_folder}\n\n")

    txtfile.write("COMPROBANTES RENOMBRADOS:\n")
    txtfile.write(f"  - PDFs individuales: {pdfs_individuales}\n")
    txtfile.write(f"  - Paginas extraidas de masivos: {pdfs_masivos_extraidos}\n")
    txtfile.write(f"  - Total comprobantes renombrados: {comprobantes_renombrados}\n\n")

    txtfile.write("FORMATO DISTINTO AL ESPERADO:\n")
    txtfile.write(f"  - Paginas extraidas de masivos (sin OP): {pdfs_formato_distinto_extraidos}\n")
    txtfile.write(f"  - PDFs individuales (sin patron): {pdfs_no_encontro_patron}\n")
    txtfile.write(f"  - Total formato distinto: {total_formato_distinto}\n\n")

    txtfile.write("HOJAS OMITIDAS:\n")
    txtfile.write(f"  - Paginas listado informativo (masivos): {paginas_masivo_omitidas}\n")
    txtfile.write(f"  - PDFs no editables (imagen): {pdfs_no_editables}\n")
    txtfile.write(f"  - Total hojas omitidas: {hojas_omitidas}\n\n")

    txtfile.write(f"TOTAL DE HOJAS EN ARCHIVOS: {total_hojas}\n\n")

    txtfile.write("VERIFICACION:\n")
    txtfile.write(f"  {comprobantes_renombrados} + {total_formato_distinto} + {hojas_omitidas} = {comprobantes_renombrados + total_formato_distinto + hojas_omitidas}\n\n")

    if comprobantes_renombrados + total_formato_distinto + hojas_omitidas == total_hojas:
        txtfile.write("  ✓ OK - VERIFICACION EXITOSA\n")
    else:
        txtfile.write("  ✗ ERROR - Las sumas no coinciden\n")

print(f"✓ Reporte TXT: {txt_path}\n")

if error_files:
    print(f"\n⚠ {len(error_files)} archivos con errores o sin patrón:")
    for path, fname, folder in error_files[:10]:  # Mostrar máximo 10
        print(f"   - {fname} en {os.path.relpath(folder, root_folder)}")
    if len(error_files) > 10:
        print(f"   ... y {len(error_files) - 10} más")

print(f"\n✓ Proceso completado")