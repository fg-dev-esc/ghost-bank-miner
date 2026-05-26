#!/usr/bin/env python3
"""
Script para consultar el estado del CSV maestro
Permite ver estadísticas y buscar archivos procesados
"""

import os
import csv
import sys
from collections import Counter

def cargar_csv(csv_path):
    """Carga el CSV maestro y retorna lista de registros"""
    registros = []
    if not os.path.exists(csv_path):
        print(f"ERROR: No se encontró el archivo {csv_path}")
        return registros

    try:
        with open(csv_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                registros.append(row)
        return registros
    except Exception as e:
        print(f"ERROR al leer CSV: {e}")
        return []

def mostrar_estadisticas(registros):
    """Muestra estadísticas generales del CSV"""
    print("\n" + "="*80)
    print("ESTADÍSTICAS DEL CSV MAESTRO")
    print("="*80)

    total = len(registros)
    print(f"\nTotal de registros: {total}")

    # Contar por estatus
    estatus_counter = Counter(r.get('Estatus', 'Sin estatus') for r in registros)
    print(f"\nPor Estatus:")
    for estatus, count in estatus_counter.most_common():
        porcentaje = (count / total * 100) if total > 0 else 0
        print(f"  {estatus:30s}: {count:5d} ({porcentaje:5.1f}%)")

    # Archivos con hash
    con_hash = sum(1 for r in registros if r.get('Hash Archivo', '').strip())
    print(f"\nArchivos con hash calculado: {con_hash} ({con_hash/total*100:.1f}%)")

    # Duplicados por nombre
    nombres = [r.get('Nombre Nuevo', '') for r in registros if r.get('Nombre Nuevo', '')]
    duplicados = [nombre for nombre, count in Counter(nombres).items() if count > 1]
    print(f"\nNombres duplicados detectados: {len(duplicados)}")
    if duplicados[:5]:
        print("  Ejemplos:")
        for nombre in duplicados[:5]:
            print(f"    - {nombre}")

def buscar_archivo(registros, termino):
    """Busca archivos que coincidan con el término"""
    print("\n" + "="*80)
    print(f"BÚSQUEDA: '{termino}'")
    print("="*80)

    resultados = [
        r for r in registros
        if termino.lower() in r.get('Nombre Original', '').lower()
        or termino.lower() in r.get('Nombre Nuevo', '').lower()
        or termino.lower() in r.get('Ruta Original', '').lower()
    ]

    if not resultados:
        print("\nNo se encontraron resultados.")
        return

    print(f"\nSe encontraron {len(resultados)} resultados:\n")
    for r in resultados[:10]:  # Mostrar máximo 10
        print(f"ID: {r.get('ID', 'N/A')}")
        print(f"  Nombre Original: {r.get('Nombre Original', 'N/A')}")
        print(f"  Nombre Nuevo: {r.get('Nombre Nuevo', 'N/A')}")
        print(f"  Estatus: {r.get('Estatus', 'N/A')}")
        print(f"  Ruta: {r.get('Ruta Original', 'N/A')}")
        print()

    if len(resultados) > 10:
        print(f"... y {len(resultados) - 10} resultados más.")

def listar_ultimos(registros, n=10):
    """Lista los últimos N registros procesados"""
    print("\n" + "="*80)
    print(f"ÚLTIMOS {n} ARCHIVOS PROCESADOS")
    print("="*80 + "\n")

    ultimos = sorted(registros, key=lambda r: int(r.get('ID', 0)), reverse=True)[:n]

    for r in ultimos:
        print(f"ID: {r.get('ID', 'N/A')}")
        print(f"  Nombre Original: {r.get('Nombre Original', 'N/A')}")
        print(f"  Nombre Nuevo: {r.get('Nombre Nuevo', 'N/A')}")
        print(f"  Estatus: {r.get('Estatus', 'N/A')}")
        print()

def mostrar_errores(registros):
    """Muestra archivos con errores o sin patrón"""
    print("\n" + "="*80)
    print("ARCHIVOS CON PROBLEMAS")
    print("="*80 + "\n")

    errores = [
        r for r in registros
        if 'Error' in r.get('Estatus', '')
        or 'No se encontró patrón' in r.get('Estatus', '')
    ]

    if not errores:
        print("No hay archivos con errores.")
        return

    print(f"Total de archivos con problemas: {len(errores)}\n")

    for r in errores[:20]:  # Mostrar máximo 20
        print(f"ID: {r.get('ID', 'N/A')}")
        print(f"  Nombre: {r.get('Nombre Original', 'N/A')}")
        print(f"  Estatus: {r.get('Estatus', 'N/A')}")
        print(f"  Ruta: {r.get('Ruta Original', 'N/A')}")
        print()

    if len(errores) > 20:
        print(f"... y {len(errores) - 20} errores más.")

def menu_principal():
    """Muestra menú interactivo"""
    folder = os.getcwd()
    csv_path = os.path.join(folder, 'resumen-de-extracción.csv')

    registros = cargar_csv(csv_path)
    if not registros:
        return

    while True:
        print("\n" + "="*80)
        print("CONSULTA DE CSV MAESTRO")
        print("="*80)
        print("\n1. Ver estadísticas generales")
        print("2. Buscar archivo")
        print("3. Ver últimos archivos procesados")
        print("4. Ver archivos con errores")
        print("5. Salir")

        opcion = input("\nSelecciona una opción: ").strip()

        if opcion == '1':
            mostrar_estadisticas(registros)
        elif opcion == '2':
            termino = input("\nIngresa término de búsqueda: ").strip()
            if termino:
                buscar_archivo(registros, termino)
        elif opcion == '3':
            try:
                n = input("\n¿Cuántos registros mostrar? (default: 10): ").strip()
                n = int(n) if n else 10
                listar_ultimos(registros, n)
            except ValueError:
                print("Número inválido, usando 10 por defecto.")
                listar_ultimos(registros, 10)
        elif opcion == '4':
            mostrar_errores(registros)
        elif opcion == '5':
            print("\nSaliendo...")
            break
        else:
            print("\nOpción inválida.")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Modo CLI con argumentos
        comando = sys.argv[1]
        folder = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
        csv_path = os.path.join(folder, 'resumen-de-extracción.csv')

        registros = cargar_csv(csv_path)
        if not registros:
            sys.exit(1)

        if comando == 'stats':
            mostrar_estadisticas(registros)
        elif comando == 'buscar' and len(sys.argv) > 2:
            buscar_archivo(registros, sys.argv[2])
        elif comando == 'ultimos':
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            listar_ultimos(registros, n)
        elif comando == 'errores':
            mostrar_errores(registros)
        else:
            print("Uso: python consultar-csv.py [stats|buscar|ultimos|errores] [argumentos]")
    else:
        # Modo interactivo
        menu_principal()
