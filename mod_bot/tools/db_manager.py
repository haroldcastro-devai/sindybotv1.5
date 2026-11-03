#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Tuple, Any, Optional
import json
import logging
import os

from dotenv import load_dotenv

load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DiccionarioDB")

class GestorDB:
    """
    Gestor de conexiones y operaciones con bases de datos para el diccionario.
    """
    
    def __init__(self):
        """Inicializa el gestor de bases de datos."""
        local_pwd = os.environ.get("DB_PASSWORD")
        if not local_pwd:
            raise ValueError("DB_PASSWORD no configurada en el entorno")
        self.local_config = {
            "host": os.environ.get("DB_HOST", "localhost"),
            "user": os.environ.get("DB_USER", "adminsbot"),
            "password": local_pwd,
            "database": os.environ.get("DB_NAME", "auto_sbot"),
        }

        self.cloud_config = None
        if all(
            os.environ.get(k)
            for k in ("AWS_DB_HOST", "AWS_DB_USER", "AWS_DB_PASSWORD", "AWS_DB_NAME")
        ):
            self.cloud_config = {
                "host": os.environ["AWS_DB_HOST"],
                "user": os.environ["AWS_DB_USER"],
                "password": os.environ["AWS_DB_PASSWORD"],
                "database": os.environ["AWS_DB_NAME"],
            }
        
        # Conexiones
        self.db_cloud = None
        self.db_local = None
    
    def conectar(self) -> Tuple[bool, str]:
        """
        Establece conexiones a las bases de datos.
        
        Returns:
            Tuple[bool, str]: (éxito, mensaje de estado)
        """
        mensaje = []
        
        # Intentar conectar a BD en la nube (solo si hay variables AWS_DB_*)
        if self.cloud_config:
            try:
                self.db_cloud = mysql.connector.connect(**self.cloud_config)
                if self.db_cloud.is_connected():
                    mensaje.append("Nube: Conectada")
                    self._crear_tabla(self.db_cloud)
                else:
                    mensaje.append("Nube: Error de conexión")
            except Error as e:
                logger.error(f"Error conectando a BD nube: {e}")
                mensaje.append(f"Nube: Error ({str(e)[:30]}...)")
        else:
            mensaje.append("Nube: omitida (sin AWS_DB_* en entorno)")
        
        # Intentar conectar a BD local
        try:
            self.db_local = mysql.connector.connect(**self.local_config)
            if self.db_local.is_connected():
                mensaje.append("Local: Conectada")
                # Crear tabla si no existe
                self._crear_tabla(self.db_local)
            else:
                mensaje.append("Local: Error de conexión")
        except Error as e:
            logger.error(f"Error conectando a BD local: {e}")
            mensaje.append(f"Local: Error ({str(e)[:30]}...)")
        
        # Determinar si al menos una conexión fue exitosa
        conectado = (self.db_cloud and self.db_cloud.is_connected()) or (self.db_local and self.db_local.is_connected())
        
        return conectado, " | ".join(mensaje)
    
    def _crear_tabla(self, conexion) -> bool:
        """
        Crea la tabla de diccionario si no existe.
        
        Args:
            conexion: Conexión a base de datos
            
        Returns:
            bool: True si la operación fue exitosa
        """
        if not conexion or not conexion.is_connected():
            return False
        
        try:
            cursor = conexion.cursor()
            
            # SQL para crear tabla si no existe
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
            logger.error(f"Error creando tabla: {e}")
            return False
    
    def cargar_diccionario(self) -> Tuple[Dict[str, str], str]:
        """
        Carga el diccionario desde la base de datos.
        Intenta primero en la nube, luego en la local.
        
        Returns:
            Tuple[Dict[str, str], str]: (diccionario, origen de los datos)
        """
        diccionario = {}
        origen = "No disponible"
        
        # Intentar cargar desde la nube primero
        if self.db_cloud and self.db_cloud.is_connected():
            try:
                cursor = self.db_cloud.cursor()
                query = "SELECT palabra_original, palabra_corregida FROM diccionario WHERE activo = TRUE"
                cursor.execute(query)
                
                for (original, corregida) in cursor:
                    diccionario[original] = corregida
                
                cursor.close()
                
                if diccionario:
                    origen = "Base de datos nube"
                    logger.info(f"Diccionario cargado desde BD nube: {len(diccionario)} entradas")
                    return diccionario, origen
            except Error as e:
                logger.error(f"Error cargando diccionario desde BD nube: {e}")
        
        # Si falla o está vacío, intentar con la BD local
        if self.db_local and self.db_local.is_connected():
            try:
                cursor = self.db_local.cursor()
                query = "SELECT palabra_original, palabra_corregida FROM diccionario WHERE activo = TRUE"
                cursor.execute(query)
                
                for (original, corregida) in cursor:
                    diccionario[original] = corregida
                
                cursor.close()
                
                if diccionario:
                    origen = "Base de datos local"
                    logger.info(f"Diccionario cargado desde BD local: {len(diccionario)} entradas")
                    return diccionario, origen
            except Error as e:
                logger.error(f"Error cargando diccionario desde BD local: {e}")
        
        return diccionario, origen
    
    def guardar_diccionario(self, diccionario: Dict[str, str]) -> Tuple[bool, str]:
        """
        Guarda el diccionario en ambas bases de datos.
        
        Args:
            diccionario: Diccionario de correcciones
            
        Returns:
            Tuple[bool, str]: (éxito, mensaje de resultado)
        """
        resultados = []
        exito = False
        
        # Guardar en BD nube
        if self.db_cloud and self.db_cloud.is_connected():
            try:
                resultado_nube = self._guardar_en_bd(self.db_cloud, diccionario)
                resultados.append(f"Nube: {resultado_nube}")
                exito = True
            except Error as e:
                logger.error(f"Error guardando en BD nube: {e}")
                resultados.append(f"Nube: Error - {str(e)[:50]}")
        else:
            resultados.append("Nube: Sin conexión")
        
        # Guardar en BD local
        if self.db_local and self.db_local.is_connected():
            try:
                resultado_local = self._guardar_en_bd(self.db_local, diccionario)
                resultados.append(f"Local: {resultado_local}")
                exito = True
            except Error as e:
                logger.error(f"Error guardando en BD local: {e}")
                resultados.append(f"Local: Error - {str(e)[:50]}")
        else:
            resultados.append("Local: Sin conexión")
        
        return exito, " | ".join(resultados)
    
    def _guardar_en_bd(self, conexion, diccionario: Dict[str, str]) -> str:
        """
        Guarda el diccionario en una base de datos específica.
        
        Args:
            conexion: Conexión a la base de datos
            diccionario: Diccionario de correcciones
            
        Returns:
            str: Mensaje de resultado
        """
        if not conexion or not conexion.is_connected():
            return "Sin conexión"
        
        try:
            cursor = conexion.cursor()
            
            # Truncar tabla para comenzar fresco
            cursor.execute("DELETE FROM diccionario")
            
            # Insertar nuevos datos
            insert_query = "INSERT INTO diccionario (palabra_original, palabra_corregida) VALUES (%s, %s)"
            valores = [(original, correccion) for original, correccion in diccionario.items()]
            
            cursor.executemany(insert_query, valores)
            conexion.commit()
            
            filas_afectadas = cursor.rowcount
            cursor.close()
            
            return f"Guardado exitoso ({filas_afectadas} entradas)"
        except Error as e:
            logger.error(f"Error en _guardar_en_bd: {e}")
            raise
    
    def cerrar_conexiones(self):
        """Cierra las conexiones a las bases de datos."""
        if self.db_cloud and self.db_cloud.is_connected():
            self.db_cloud.close()
            
        if self.db_local and self.db_local.is_connected():
            self.db_local.close()