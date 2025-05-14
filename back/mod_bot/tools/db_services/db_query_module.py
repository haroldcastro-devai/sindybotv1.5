#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import json
import mysql.connector
from mysql.connector import Error
from typing import Dict, Any, Optional, Tuple
from db_logger import db_logger, log_query, log_db_info

# Configuración del logger
logger = logging.getLogger(__name__)

class DatabaseQuerier:
    """
    Módulo para consultar guiones y tarifas directamente de la base de datos.
    """
    
    def __init__(self, host=None, user=None, password=None, database=None):
        """
        Inicializa la conexión a la base de datos.
        Si no se proporcionan parámetros, usa valores por defecto.
        """
        # Valores por defecto
        self.config = {
            'host': host or 'localhost',
            'user': user or 'adminsbot',
            'password': password or '&-4GWwgiw9UfFfOp',
            'database': database or 'auto_sbot'
        }
        self.connection = None
        self.cursor = None
        
        # Registrar configuración inicial
        db_logger.info(f"Inicializando DatabaseQuerier con base de datos: {self.config['database']} en {self.config['host']}")
    
    def connect(self) -> bool:
        """
        Establece la conexión a la base de datos.
        
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario.
        """
        try:
            db_logger.info(f"Intentando conectar a MySQL: {self.config['host']}/{self.config['database']}")
            self.connection = mysql.connector.connect(**self.config)
            
            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                db_logger.info(f"Conexión exitosa a MySQL: {self.config['host']}/{self.config['database']}")
                
                # Obtener información del servidor para el log
                server_info = self.connection.get_server_info()
                db_logger.info(f"Información del servidor MySQL: {server_info}")
                
                return True
            
            db_logger.error(f"No se pudo conectar a MySQL: la conexión no está activa")
            return False
            
        except Error as e:
            db_logger.error(f"Error al conectar a MySQL: {e}")
            return False
    
    def close(self):
        """Cierra la conexión a la base de datos."""
        if self.cursor:
            self.cursor.close()
            db_logger.info("Cursor cerrado")
            
        if self.connection and self.connection.is_connected():
            self.connection.close()
            db_logger.info("Conexión a MySQL cerrada")
    
    def fetch_guiones(self) -> Dict[str, Any]:
        """
        Consulta los guiones desde la base de datos y los formatea
        en la misma estructura que tenían en el archivo JSON.
        
        Returns:
            Dict: Guiones en formato similar al archivo guionV2.json
        """
        db_logger.info("Iniciando fetch_guiones() - Consultando guiones desde la base de datos")
        
        if not self.connection or not self.cursor:
            db_logger.info("No hay conexión activa, intentando conectar")
            if not self.connect():
                db_logger.error("No se pudo conectar a la base de datos")
                return {}
        
        guiones_data = {"GASERAS_GUIONES": {}}
        
        try:
            # Primero obtenemos las gaseras
            query = "SELECT id, nombre, codigo FROM gaseras WHERE activo = 1"
            log_query(query)
            self.cursor.execute(query)
            gaseras = self.cursor.fetchall()
            log_query(query, result=f"{len(gaseras)} gaseras encontradas")
            
            for gasera in gaseras:
                gasera_id = gasera['id']
                gasera_nombre = gasera['nombre']
                guiones_data["GASERAS_GUIONES"][gasera_nombre] = {"aseguradoras": []}
                
                # Obtenemos las aseguradoras relacionadas con esta gasera
                query = """
                    SELECT a.id, a.nombre 
                    FROM aseguradoras a
                    JOIN gaseras_aseguradoras ga ON a.id = ga.aseguradora_id
                    WHERE ga.gasera_id = %s AND a.activo = 1 AND ga.activo = 1
                """
                params = (gasera_id,)
                log_query(query, params)
                self.cursor.execute(query, params)
                aseguradoras = self.cursor.fetchall()
                log_query(query, params, result=f"{len(aseguradoras)} aseguradoras encontradas para gasera {gasera_nombre}")
                
                for aseguradora in aseguradoras:
                    aseguradora_id = aseguradora['id']
                    aseguradora_nombre = aseguradora['nombre']
                    aseguradora_data = {"nombre": aseguradora_nombre, "planes": {}}
                    
                    # Obtenemos los planes relacionados
                    query = """
                        SELECT p.id, p.nombre
                        FROM planes p
                        JOIN gaseras_aseguradoras ga ON p.gasera_aseguradora_id = ga.id
                        WHERE ga.gasera_id = %s AND ga.aseguradora_id = %s AND p.activo = 1
                    """
                    params = (gasera_id, aseguradora_id)
                    log_query(query, params)
                    self.cursor.execute(query, params)
                    planes = self.cursor.fetchall()
                    log_query(query, params, result=f"{len(planes)} planes encontrados para gasera {gasera_nombre} y aseguradora {aseguradora_nombre}")
                    
                    for plan in planes:
                        plan_id = plan['id']
                        plan_nombre = plan['nombre']
                        
                        # Obtenemos el guion asociado a este plan
                        query = """
                            SELECT contenido 
                            FROM guiones_planes 
                            WHERE plan_id = %s AND activo = 1
                        """
                        params = (plan_id,)
                        log_query(query, params)
                        self.cursor.execute(query, params)
                        guion_result = self.cursor.fetchone()
                        
                        if guion_result and guion_result['contenido']:
                            log_query(query, params, result="Guion encontrado")
                            # Para mantener la estructura esperada por el código actual
                            plan_data = {
                                "nombre": plan_nombre,
                                "guion": guion_result['contenido']
                            }
                            aseguradora_data["planes"][plan_nombre] = plan_data
                        else:
                            log_query(query, params, result="No se encontró guion")
                    
                    # Solo añadimos aseguradoras que tienen planes con guiones
                    if aseguradora_data["planes"]:
                        guiones_data["GASERAS_GUIONES"][gasera_nombre]["aseguradoras"].append(aseguradora_data)
            
            # Registrar resumen de guiones recuperados
            gaseras_count = len(guiones_data["GASERAS_GUIONES"])
            aseguradoras_count = sum(len(g["aseguradoras"]) for g in guiones_data["GASERAS_GUIONES"].values())
            planes_count = sum(sum(len(a["planes"]) for a in g["aseguradoras"]) 
                              for g in guiones_data["GASERAS_GUIONES"].values())
            
            db_logger.info(f"fetch_guiones finalizado: {gaseras_count} gaseras, {aseguradoras_count} aseguradoras, {planes_count} planes con guiones")
            return guiones_data
            
        except Error as e:
            db_logger.error(f"Error consultando guiones: {e}")
            import traceback
            db_logger.error(traceback.format_exc())
            return {}
    
    def fetch_tarifas(self) -> Dict[str, Any]:
        """
        Consulta las tarifas desde la base de datos y las formatea
        en la misma estructura que tenían en el archivo JSON.
        
        Returns:
            Dict: Tarifas en formato similar al archivo tarifasV2.json
        """
        db_logger.info("Iniciando fetch_tarifas() - Consultando tarifas desde la base de datos")
        
        if not self.connection or not self.cursor:
            db_logger.info("No hay conexión activa, intentando conectar")
            if not self.connect():
                db_logger.error("No se pudo conectar a la base de datos")
                return {}
        
        tarifas_data = {"GASERAS_TARIFAS_INDEMNIZACION_COVERTURA": {}}
        
        try:
            # Obtenemos las gaseras
            query = "SELECT id, nombre, codigo FROM gaseras WHERE activo = 1"
            log_query(query)
            self.cursor.execute(query)
            gaseras = self.cursor.fetchall()
            log_query(query, result=f"{len(gaseras)} gaseras encontradas")
            
            for gasera in gaseras:
                gasera_id = gasera['id']
                gasera_nombre = gasera['nombre']
                tarifas_data["GASERAS_TARIFAS_INDEMNIZACION_COVERTURA"][gasera_nombre] = {"aseguradoras": []}
                
                # Obtenemos las aseguradoras relacionadas con esta gasera
                query = """
                    SELECT a.id, a.nombre 
                    FROM aseguradoras a
                    JOIN gaseras_aseguradoras ga ON a.id = ga.aseguradora_id
                    WHERE ga.gasera_id = %s AND a.activo = 1 AND ga.activo = 1
                """
                params = (gasera_id,)
                log_query(query, params)
                self.cursor.execute(query, params)
                aseguradoras = self.cursor.fetchall()
                log_query(query, params, result=f"{len(aseguradoras)} aseguradoras encontradas para gasera {gasera_nombre}")
                
                for aseguradora in aseguradoras:
                    aseguradora_id = aseguradora['id']
                    aseguradora_nombre = aseguradora['nombre']
                    aseguradora_data = {"nombre": aseguradora_nombre, "planes": {}}
                    
                    # Obtenemos la relación gasera-aseguradora
                    query = """
                        SELECT id 
                        FROM gaseras_aseguradoras 
                        WHERE gasera_id = %s AND aseguradora_id = %s
                    """
                    params = (gasera_id, aseguradora_id)
                    log_query(query, params)
                    self.cursor.execute(query, params)
                    ga_result = self.cursor.fetchone()
                    
                    if ga_result:
                        ga_id = ga_result['id']
                        log_query(query, params, result=f"Relación encontrada con ID {ga_id}")
                        
                        # Obtenemos los planes relacionados
                        query = """
                            SELECT id, nombre, tarifa_mensual, prima_anual, 
                                   detalles_indemnizacion, edad_ingreso, edad_permanencia
                            FROM planes 
                            WHERE gasera_aseguradora_id = %s AND activo = 1
                        """
                        params = (ga_id,)
                        log_query(query, params)
                        self.cursor.execute(query, params)
                        planes = self.cursor.fetchall()
                        log_query(query, params, result=f"{len(planes)} planes encontrados")
                        
                        for plan in planes:
                            plan_nombre = plan['nombre']
                            
                            # Mostrar información completa del plan para diagnóstico
                            db_logger.info(f"Procesando plan: {plan_nombre} (ID: {plan['id']})")
                            db_logger.info(f"  tarifa_mensual: {plan['tarifa_mensual']}")
                            db_logger.info(f"  prima_anual: {plan['prima_anual']}")
                            db_logger.info(f"  edad_ingreso: {plan['edad_ingreso']}")
                            db_logger.info(f"  edad_permanencia: {plan['edad_permanencia']}")
                            db_logger.info(f"  detalles_indemnizacion: {type(plan['detalles_indemnizacion'])}")
                            
                            # Construir datos de tarifa según el formato esperado
                            plan_data = {}
                            
                            # Detectar el tipo de plan para formar la clave TARIFA_X_GASERA_PLAN
                            plan_type = self._extract_plan_type(plan_nombre)
                            tarifa_key = f"TARIFA_{plan_type}_GASERA_PLAN"
                            indem_key = f"INDEMNIZACION_{plan_type}_GASERA_PLAN"
                            
                            db_logger.info(f"  tipo_plan: {plan_type}")
                            db_logger.info(f"  tarifa_key: {tarifa_key}")
                            db_logger.info(f"  indem_key: {indem_key}")
                            
                            # Agregar los datos básicos
                            plan_data[tarifa_key] = plan['tarifa_mensual']
                            plan_data["PRIMA_ANUAL"] = plan['prima_anual']
                            plan_data["EDAD_INGRESO"] = plan['edad_ingreso']
                            plan_data["EDAD_PERMANENCIA"] = plan['edad_permanencia']
                            
                            # Procesar detalles de indemnización
                            if plan['detalles_indemnizacion']:
                                # Si es un JSON almacenado como string, convertirlo
                                if isinstance(plan['detalles_indemnizacion'], str):
                                    try:
                                        indem_data = json.loads(plan['detalles_indemnizacion'])
                                        plan_data[indem_key] = indem_data
                                        db_logger.info(f"  detalles_indemnizacion parseado: {indem_data}")
                                    except json.JSONDecodeError as json_err:
                                        plan_data[indem_key] = plan['detalles_indemnizacion']
                                        db_logger.error(f"  Error parseando detalles_indemnizacion: {json_err}")
                                else:
                                    plan_data[indem_key] = plan['detalles_indemnizacion']
                                    db_logger.info(f"  detalles_indemnizacion no es string: {plan['detalles_indemnizacion']}")
                            
                            # Agregar datos específicos de indemnización si existen claves adicionales
                            if isinstance(plan['detalles_indemnizacion'], dict):
                                for key, value in plan['detalles_indemnizacion'].items():
                                    if key.startswith("INDEMNIZACION_"):
                                        plan_data[key] = value
                                        db_logger.info(f"  Clave adicional encontrada: {key}={value}")
                            
                            aseguradora_data["planes"][plan_nombre] = plan_data
                    else:
                        log_query(query, params, result="No se encontró relación gasera-aseguradora")
                    
                    # Solo añadimos aseguradoras que tienen planes
                    if aseguradora_data["planes"]:
                        tarifas_data["GASERAS_TARIFAS_INDEMNIZACION_COVERTURA"][gasera_nombre]["aseguradoras"].append(aseguradora_data)
            
            # Registrar resumen de tarifas recuperadas
            gaseras_count = len(tarifas_data["GASERAS_TARIFAS_INDEMNIZACION_COVERTURA"])
            aseguradoras_count = sum(len(g["aseguradoras"]) for g in tarifas_data["GASERAS_TARIFAS_INDEMNIZACION_COVERTURA"].values())
            planes_count = sum(sum(len(a["planes"]) for a in g["aseguradoras"]) 
                              for g in tarifas_data["GASERAS_TARIFAS_INDEMNIZACION_COVERTURA"].values())
            
            db_logger.info(f"fetch_tarifas finalizado: {gaseras_count} gaseras, {aseguradoras_count} aseguradoras, {planes_count} planes con tarifas")
            return tarifas_data
            
        except Error as e:
            db_logger.error(f"Error consultando tarifas: {e}")
            import traceback
            db_logger.error(traceback.format_exc())
            return {}
    
    def _extract_plan_type(self, plan_name: str) -> str:
        """
        Extrae el tipo de plan a partir del nombre del plan.
        Esta función replica la lógica de extracción de tipo de plan del código original.
        
        Args:
            plan_name: Nombre del plan
            
        Returns:
            str: Tipo de plan para formar las claves de tarifa e indemnización
        """
        plan_name = plan_name.upper()
        
        if "PRACTISEGURO" in plan_name:
            return "PRACTISEGURO"
        elif "MASCOTAS" in plan_name:
            return "MASCOTAS"
        elif "FUNERARIO" in plan_name:
            return "FUNERARIO"
        elif "FUTURO PROTEGIDO" in plan_name:
            return "FUTUROPROTEGIDOPLUS"
        elif "FACTURA PROTEGIDA" in plan_name:
            return "FACTURAPROTEGIDA"
        elif "SALVA FACTURA" in plan_name:
            return "SALVAFACTURA"
        else:
            # Convertir el nombre a un formato apto para nombres de campo
            import re
            return re.sub(r'\W+', '', plan_name)