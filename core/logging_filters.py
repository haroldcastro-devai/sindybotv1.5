"""
Filtros personalizados para logging en SBOT.
"""

import logging
import re

class LimitGetRequestsFilter(logging.Filter):
    """
    Filtro personalizado para limitar la cantidad de logs de peticiones GET consecutivas.
    Solo permite mostrar un número máximo de logs GET consecutivos, 
    manteniendo visible el resto de los logs del sistema.
    """
    
    def __init__(self, max_consecutive=2):
        """
        Inicializa el filtro.
        
        Args:
            max_consecutive (int): Número máximo de logs GET consecutivos a mostrar.
        """
        super().__init__()
        self.max_consecutive = max_consecutive
        self.get_count = 0
        self.get_pattern = re.compile(r'"GET\s+.*?\s+HTTP/\d\.\d"\s+\d{3}')
    
    def filter(self, record):
        """
        Filtra los registros de log.
        
        Args:
            record: Registro de log a filtrar.
            
        Returns:
            bool: True si el registro debe mostrarse, False en caso contrario.
        """
        # Si el mensaje no es un log formateado (puede ser None), permitirlo
        if not hasattr(record, 'msg') or record.msg is None:
            self.get_count = 0  # Resetear contador
            return True
            
        # Convertir el mensaje a string en caso de que no lo sea
        msg_str = str(record.msg)
        
        # Verificar si es un log de petición GET
        if self.get_pattern.search(msg_str):
            self.get_count += 1
            # Permitir solo hasta el número máximo consecutivo
            return self.get_count <= self.max_consecutive
        else:
            # No es un log GET, resetear contador y permitir
            self.get_count = 0
            return True