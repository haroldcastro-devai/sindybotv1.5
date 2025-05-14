#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from typing import Dict, List, Tuple, Any

class CorrectorTexto:
    """
    Clase que maneja la corrección de texto utilizando un diccionario.
    Soporta corrección de palabras individuales y frases completas.
    """
    
    def __init__(self, diccionario: Dict[str, str] = None):
        """
        Inicializa el corrector con un diccionario opcional.
        
        Args:
            diccionario: Diccionario de correcciones {original: corregido}
        """
        self.diccionario = diccionario or {}
        # Ordenamos el diccionario por longitud (descendente) para que las frases más largas
        # se reemplacen primero, evitando reemplazos parciales incorrectos
        self.entradas_ordenadas = []
        self.actualizar_entradas_ordenadas()
    
    def actualizar_entradas_ordenadas(self):
        """Actualiza la lista ordenada de entradas del diccionario por longitud"""
        self.entradas_ordenadas = sorted(
            self.diccionario.items(), 
            key=lambda x: len(x[0]), 
            reverse=True
        )
    
    def corregir_texto(self, texto: str) -> str:
        """
        Corrige un texto utilizando el diccionario de correcciones.
        Maneja tanto palabras individuales como frases completas.
        También detecta palabras incorrectamente unidas.
        
        Args:
            texto: Texto a corregir
            
        Returns:
            str: Texto corregido
        """
        if not self.diccionario:
            return texto
        
        texto_corregido = texto
        
        # Primero procesamos para detectar palabras incorrectamente unidas
        for original, correccion in self.entradas_ordenadas:
            # Si la corrección tiene espacios pero el original no (palabra compuesta incorrecta)
            if ' ' in correccion and ' ' not in original:
                # Buscamos la palabra en el texto (sin usar límites de palabra estrictos)
                patron = re.escape(original)
                texto_corregido = self._reemplazo_preservando_capitalizacion(
                    texto_corregido, patron, original, correccion
                )
        
        # Segundo, corregimos frases completas (ordenadas de más largas a más cortas)
        for original, correccion in self.entradas_ordenadas:
            if ' ' in original:  # Es una frase
                # Usamos una expresión regular que respeta límites de palabra
                patron = r'\b' + re.escape(original) + r'\b'
                texto_corregido = self._reemplazo_preservando_capitalizacion(
                    texto_corregido, patron, original, correccion
                )
        
        # Finalmente procesamos palabra por palabra para palabras individuales
        palabras = texto_corregido.split()
        resultado = []
        
        for palabra in palabras:
            palabra_original = palabra
            
            # Extraer palabra limpia (sin puntuación) para buscar en el diccionario
            prefijo, palabra_central, sufijo = self._extraer_partes_palabra(palabra_original)
            palabra_limpia = palabra_central.lower()
            
            # Verificar si la palabra está en el diccionario
            if palabra_limpia and ' ' not in palabra_limpia and palabra_limpia in self.diccionario:
                correccion = self._aplicar_capitalizacion(
                    self.diccionario[palabra_limpia], 
                    palabra_central
                )
                palabra_corregida = prefijo + correccion + sufijo
                resultado.append(palabra_corregida)
            else:
                resultado.append(palabra_original)
        
        return ' '.join(resultado)
    
    def _reemplazo_preservando_capitalizacion(self, texto: str, patron: str, original: str, correccion: str) -> str:
        """
        Reemplaza ocurrencias de un patrón preservando la capitalización.
        
        Args:
            texto: Texto donde realizar el reemplazo
            patron: Patrón de búsqueda (expresión regular)
            original: Texto original a reemplazar
            correccion: Texto de reemplazo
            
        Returns:
            str: Texto con reemplazos realizados
        """
        def reemplazo(coincidencia):
            texto_coincidencia = coincidencia.group(0)
            
            # Verificar capitalización
            if texto_coincidencia.isupper():
                return correccion.upper()
            elif texto_coincidencia[0].isupper():
                return correccion.capitalize()
            else:
                return correccion
        
        return re.sub(patron, reemplazo, texto)
    
    def _extraer_partes_palabra(self, palabra: str) -> Tuple[str, str, str]:
        """
        Extrae prefijo (puntuación inicial), parte central y sufijo (puntuación final) de una palabra.
        
        Args:
            palabra: Palabra a procesar
            
        Returns:
            Tuple[str, str, str]: (prefijo, parte_central, sufijo)
        """
        # Detectar prefijos (puntuación al inicio)
        match_prefix = re.match(r'^([^\w]*)(.*)', palabra)
        if match_prefix:
            prefijo = match_prefix.group(1)
            palabra_sin_prefijo = match_prefix.group(2)
        else:
            prefijo = ""
            palabra_sin_prefijo = palabra
        
        # Detectar sufijos (puntuación al final)
        match_suffix = re.match(r'(.*?)([^\w]*)$', palabra_sin_prefijo)
        if match_suffix:
            palabra_central = match_suffix.group(1)
            sufijo = match_suffix.group(2)
        else:
            palabra_central = palabra_sin_prefijo
            sufijo = ""
        
        return prefijo, palabra_central, sufijo
    
    def _aplicar_capitalizacion(self, texto: str, referencia: str) -> str:
        """
        Aplica la capitalización de la referencia al texto.
        
        Args:
            texto: Texto a modificar
            referencia: Texto de referencia para la capitalización
            
        Returns:
            str: Texto con capitalización aplicada
        """
        if not texto or not referencia:
            return texto
            
        if referencia.isupper():
            return texto.upper()
        elif referencia[0].isupper():
            if len(texto) > 1:
                return texto[0].upper() + texto[1:]
            return texto.upper()
        return texto