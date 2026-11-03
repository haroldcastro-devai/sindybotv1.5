#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import mysql.connector
from mysql.connector import Error
import sys
import os
import json

def conectar_bd(config):
    """Establece conexión a la base de datos"""
    try:
        conexion = mysql.connector.connect(**config)
        if conexion.is_connected():
            print(f"Conectado a {config['host']} - {config['database']}")
            return conexion
        return None
    except Error as e:
        print(f"Error al conectar a {config['host']}: {e}")
        return None

def crear_tabla_diccionario(conexion):
    """Crea la tabla de diccionario si no existe"""
    if not conexion or not conexion.is_connected():
        return False
        
    try:
        cursor = conexion.cursor()
        
        # Crear tabla si no existe
        query = """
        CREATE TABLE IF NOT EXISTS diccionario (
            id INT AUTO_INCREMENT PRIMARY KEY,
            palabra_original VARCHAR(255) NOT NULL,
            palabra_corregida VARCHAR(255) NOT NULL,
            categoria VARCHAR(100) DEFAULT 'general',
            activo BOOLEAN DEFAULT TRUE,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY idx_palabra_original (palabra_original)
        )
        """
        
        cursor.execute(query)
        conexion.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"Error al crear tabla: {e}")
        return False

def importar_desde_texto(ruta_archivo, conexiones):
    """Importa diccionario desde archivo de texto"""
    # Verificar si el archivo existe
    if not os.path.exists(ruta_archivo):
        print(f"Error: El archivo {ruta_archivo} no existe")
        return False
    
    try:
        # Leer archivo
        with open(ruta_archivo, 'r', encoding='utf-8') as file:
            lineas = file.read().splitlines()
        
        # Procesar líneas
        diccionario = {}
        errores = []
        
        for i, linea in enumerate(lineas, 1):
            linea = linea.strip()
            if not linea:
                continue
            
            # Procesamos tanto el formato "palabra:corrección" como solo "palabra"
            partes = linea.split(':', 1)
            
            if len(partes) == 2:
                # Formato "palabra:corrección"
                original = partes[0].strip()
                correccion = partes[1].strip()
                
                if original and correccion:
                    diccionario[original] = correccion
            elif len(partes) == 1:
                # Formato solo "palabra"
                # Para palabras sin corrección, asumimos que la palabra es su propia corrección
                original = partes[0].strip()
                if original:
                    diccionario[original] = original
            else:
                errores.append(f"Línea {i}: Formato incorrecto: '{linea}'")
        
        # Mostrar resumen
        print(f"Procesadas {len(lineas)} líneas")
        print(f"Entradas válidas: {len(diccionario)}")
        print(f"Errores: {len(errores)}")
        
        if errores:
            print("\nDetalles de errores:")
            for e in errores[:10]:
                print(f"  - {e}")
            if len(errores) > 10:
                print(f"  - ... y {len(errores) - 10} más")
        
        # Confirmar importación
        confirmacion = input("\n¿Desea continuar con la importación? (s/n): ")
        if confirmacion.lower() != 's':
            print("Importación cancelada")
            return False
        
        # Importar a bases de datos
        for nombre, conexion in conexiones.items():
            if not conexion or not conexion.is_connected():
                print(f"Error: No hay conexión a {nombre}")
                continue
            
            try:
                cursor = conexion.cursor()
                
                # Verificar si se debe truncar la tabla
                respuesta = input(f"\n¿Desea eliminar los datos existentes en {nombre} antes de importar? (s/n): ")
                if respuesta.lower() == 's':
                    cursor.execute("DELETE FROM diccionario")
                    print(f"Datos eliminados de {nombre}")
                
                # Insertar datos
                insert_query = "INSERT INTO diccionario (palabra_original, palabra_corregida) VALUES (%s, %s) ON DUPLICATE KEY UPDATE palabra_corregida = VALUES(palabra_corregida)"
                valores = [(original, correccion) for original, correccion in diccionario.items()]
                
                cursor.executemany(insert_query, valores)
                conexion.commit()
                
                print(f"Importación a {nombre} completada: {cursor.rowcount} registros afectados")
                
                cursor.close()
            except Error as e:
                print(f"Error al importar a {nombre}: {e}")
        
        return True
    
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        return False

def importar_desde_json(ruta_archivo, conexiones):
    """Importa diccionario desde archivo JSON"""
    # Verificar si el archivo existe
    if not os.path.exists(ruta_archivo):
        print(f"Error: El archivo {ruta_archivo} no existe")
        return False
    
    try:
        # Leer archivo JSON
        with open(ruta_archivo, 'r', encoding='utf-8') as file:
            diccionario = json.load(file)
        
        # Verificar formato
        if not isinstance(diccionario, dict):
            print("Error: El archivo no contiene un diccionario válido")
            return False
        
        # Mostrar resumen
        print(f"Entradas en el archivo JSON: {len(diccionario)}")
        
        # Confirmar importación
        confirmacion = input("\n¿Desea continuar con la importación? (s/n): ")
        if confirmacion.lower() != 's':
            print("Importación cancelada")
            return False
        
        # Importar a bases de datos
        for nombre, conexion in conexiones.items():
            if not conexion or not conexion.is_connected():
                print(f"Error: No hay conexión a {nombre}")
                continue
            
            try:
                cursor = conexion.cursor()
                
                # Verificar si se debe truncar la tabla
                respuesta = input(f"\n¿Desea eliminar los datos existentes en {nombre} antes de importar? (s/n): ")
                if respuesta.lower() == 's':
                    cursor.execute("DELETE FROM diccionario")
                    print(f"Datos eliminados de {nombre}")
                
                # Insertar datos
                insert_query = "INSERT INTO diccionario (palabra_original, palabra_corregida) VALUES (%s, %s) ON DUPLICATE KEY UPDATE palabra_corregida = VALUES(palabra_corregida)"
                valores = [(original, correccion) for original, correccion in diccionario.items()]
                
                cursor.executemany(insert_query, valores)
                conexion.commit()
                
                print(f"Importación a {nombre} completada: {cursor.rowcount} registros afectados")
                
                cursor.close()
            except Error as e:
                print(f"Error al importar a {nombre}: {e}")
        
        return True
    
    except json.JSONDecodeError as e:
        print(f"Error: El archivo no es un JSON válido: {e}")
        return False
    except Exception as e:
        print(f"Error al procesar el archivo: {e}")
        return False

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Importar diccionario a bases de datos.')
    parser.add_argument('archivo', help='Ruta al archivo de diccionario (texto o JSON)')
    parser.add_argument('--formato', choices=['texto', 'json'], default='texto', 
                        help='Formato del archivo (texto o json)')
    
    args = parser.parse_args()

    from dotenv import load_dotenv

    load_dotenv()

    local_pwd = os.environ.get("DB_PASSWORD")
    if not local_pwd:
        print("Error: DB_PASSWORD no configurada en el entorno")
        return 1

    configs = {
        "Local": {
            "host": os.environ.get("DB_HOST", "localhost"),
            "user": os.environ.get("DB_USER", "adminsbot"),
            "password": local_pwd,
            "database": os.environ.get("DB_NAME", "auto_sbot"),
        }
    }
    if all(
        os.environ.get(k)
        for k in ("AWS_DB_HOST", "AWS_DB_USER", "AWS_DB_PASSWORD", "AWS_DB_NAME")
    ):
        configs["Nube"] = {
            "host": os.environ["AWS_DB_HOST"],
            "user": os.environ["AWS_DB_USER"],
            "password": os.environ["AWS_DB_PASSWORD"],
            "database": os.environ["AWS_DB_NAME"],
        }
    
    # Establecer conexiones
    conexiones = {}
    for nombre, config in configs.items():
        conexion = conectar_bd(config)
        if conexion:
            # Crear tabla si no existe
            if crear_tabla_diccionario(conexion):
                conexiones[nombre] = conexion
    
    if not conexiones:
        print("Error: No se pudo conectar a ninguna base de datos")
        return 1
    
    # Importar según formato
    if args.formato == 'texto':
        resultado = importar_desde_texto(args.archivo, conexiones)
    else:
        resultado = importar_desde_json(args.archivo, conexiones)
    
    # Cerrar conexiones
    for conexion in conexiones.values():
        if conexion and conexion.is_connected():
            conexion.close()
    
    return 0 if resultado else 1

if __name__ == "__main__":
    sys.exit(main())