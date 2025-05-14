#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import os
import sys
import threading
import logging
from typing import Dict, List, Union, Optional, Tuple, Any

# Importar módulos personalizados
# Asegúrate de que estos archivos estén en el mismo directorio o en la ruta de búsqueda
from diccionario_utils import CorrectorTexto
from db_manager import GestorDB

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DiccionarioManager")

class DiccionarioApp:
    """
    Aplicación para gestionar el diccionario de correcciones para el sistema de transcripción.
    Permite cargar, editar y guardar diccionarios de corrección que pueden incluir
    tanto palabras individuales como frases completas.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Diccionario de Correcciones")
        self.root.geometry("950x700")
        self.root.minsize(950, 700)
        
        # Variables para DB y corrector
        self.db_manager = GestorDB()
        self.diccionario = {}
        self.corrector = CorrectorTexto(self.diccionario)
        
        # Crear la interfaz
        self.create_widgets()
        
        # Intentar conexiones a bases de datos
        self.connect_databases()
        
        # Cargar diccionario actual
        self.load_dictionary_from_db()
    
    def create_widgets(self):
        """Crea todos los widgets de la interfaz gráfica"""
        
        # Frame principal con pestañas
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # === Pestaña 1: Editor de diccionario ===
        editor_frame = ttk.Frame(notebook)
        notebook.add(editor_frame, text="Editor de Diccionario")
        
        # Frame superior para opciones
        options_frame = ttk.Frame(editor_frame)
        options_frame.pack(fill='x', pady=10)
        
        # Botones de acciones
        ttk.Button(options_frame, text="Cargar desde BD", command=self.load_dictionary_from_db).pack(side='left', padx=5)
        ttk.Button(options_frame, text="Cargar JSON", command=self.load_json_file).pack(side='left', padx=5)
        ttk.Button(options_frame, text="Guardar en BD", command=self.save_dictionary_to_db).pack(side='left', padx=5)
        ttk.Button(options_frame, text="Exportar JSON", command=self.export_json_file).pack(side='left', padx=5)
        
        # Estado de conexión
        self.connection_status = ttk.Label(options_frame, text="Estado: No conectado")
        self.connection_status.pack(side='right', padx=10)
        
        # Frame para la tabla de diccionario
        table_frame = ttk.Frame(editor_frame)
        table_frame.pack(fill='both', expand=True, pady=10)
        
        # Tabla de palabras/frases
        columns = ('palabra_original', 'palabra_corregida')
        self.table = ttk.Treeview(table_frame, columns=columns, show='headings')
        self.table.heading('palabra_original', text='Texto Original')
        self.table.heading('palabra_corregida', text='Texto Corregido')
        self.table.column('palabra_original', width=250)
        self.table.column('palabra_corregida', width=250)
        self.table.pack(side='left', fill='both', expand=True)
        
        # Scrollbar para la tabla
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.table.yview)
        scrollbar.pack(side='right', fill='y')
        self.table.configure(yscrollcommand=scrollbar.set)
        
        # Evento de selección
        self.table.bind('<<TreeviewSelect>>', self.on_select_word)
        
        # Frame para edición de palabra/frase
        edit_frame = ttk.LabelFrame(editor_frame, text="Editar Entrada")
        edit_frame.pack(fill='x', pady=10, padx=5)
        
        # Campos de edición
        ttk.Label(edit_frame, text="Texto Original:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
        self.original_entry = ttk.Entry(edit_frame, width=60)
        self.original_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(edit_frame, text="Texto Corregido:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.corrected_entry = ttk.Entry(edit_frame, width=60)
        self.corrected_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Checkbox para indicar si es frase o palabra individual
        self.is_phrase_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(edit_frame, text="Es una frase o expresión", variable=self.is_phrase_var).grid(row=2, column=0, sticky='w', padx=5, pady=5)
        
        # Botones de acciones para palabras/frases
        btn_frame = ttk.Frame(edit_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Añadir / Actualizar", command=self.add_update_word).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self.delete_word).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Limpiar Campos", command=self.clear_fields).pack(side='left', padx=5)
        
        # === Pestaña 2: Entrada de texto directo ===
        text_frame = ttk.Frame(notebook)
        notebook.add(text_frame, text="Entrada de Texto")
        
        # Instrucciones
        ttk.Label(
            text_frame, 
            text="Ingrese el diccionario en formato 'texto_original:texto_corregido', una entrada por línea:"
        ).pack(anchor='w', padx=10, pady=5)
        
        ttk.Label(
            text_frame, 
            text="Nota: Puede incluir palabras individuales o frases completas"
        ).pack(anchor='w', padx=10, pady=2)
        
        # Área de texto
        self.text_area = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=25)
        self.text_area.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Botones de acción para texto
        btn_text_frame = ttk.Frame(text_frame)
        btn_text_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(btn_text_frame, text="Cargar desde Texto", command=self.load_from_text).pack(side='left', padx=5)
        ttk.Button(btn_text_frame, text="Vista Previa", command=self.preview_from_text).pack(side='left', padx=5)
        
        # === Pestaña 3: Estadísticas y Test ===
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Estadísticas y Pruebas")
        
        # Estadísticas
        stats_label_frame = ttk.LabelFrame(stats_frame, text="Estadísticas")
        stats_label_frame.pack(fill='x', padx=10, pady=10)
        
        self.stats_label = ttk.Label(stats_label_frame, text="Diccionario no cargado")
        self.stats_label.pack(padx=10, pady=10)
        
        # Área de prueba
        test_label_frame = ttk.LabelFrame(stats_frame, text="Probar Corrección")
        test_label_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        ttk.Label(test_label_frame, text="Texto Original:").pack(anchor='w', padx=10, pady=5)
        
        self.test_input = scrolledtext.ScrolledText(test_label_frame, wrap=tk.WORD, height=10)
        self.test_input.pack(fill='both', padx=10, pady=5)
        
        ttk.Button(test_label_frame, text="Corregir Texto", command=self.test_correction).pack(anchor='w', padx=10, pady=5)
        
        ttk.Label(test_label_frame, text="Texto Corregido:").pack(anchor='w', padx=10, pady=5)
        
        self.test_output = scrolledtext.ScrolledText(test_label_frame, wrap=tk.WORD, height=10)
        self.test_output.pack(fill='both', padx=10, pady=5)
        
        # Barra de estado
        self.status_bar = ttk.Label(self.root, text="Listo", relief=tk.SUNKEN, anchor='w')
        self.status_bar.pack(side='bottom', fill='x')

    def connect_databases(self):
        """Establece conexiones a las bases de datos cloud y local"""
        try:
            conectado, mensaje = self.db_manager.conectar()
            
            # Actualizar estado
            self.connection_status.config(text=mensaje)
            
            if conectado:
                self.update_status("Conexión a bases de datos establecida")
            else:
                self.update_status("No se pudo conectar a todas las bases de datos")
                
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a las bases de datos: {e}")
            self.update_status(f"Error de conexión: {e}")

    def load_dictionary_from_db(self):
        """Carga el diccionario desde la base de datos"""
        try:
            diccionario, origen = self.db_manager.cargar_diccionario()
            
            if not diccionario:
                messagebox.showwarning("Advertencia", "No se encontraron entradas en el diccionario")
                self.update_status("No hay entradas en el diccionario")
                return
            
            # Actualizar diccionario y tabla
            self.diccionario = diccionario
            self.corrector = CorrectorTexto(self.diccionario)
            
            # Actualizar tabla
            self.update_table()
            
            # Actualizar estadísticas
            self.update_statistics()
            self.update_status(f"Diccionario cargado desde {origen}: {len(self.diccionario)} entradas")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el diccionario: {e}")
            self.update_status(f"Error al cargar: {e}")

    def update_table(self):
        """Actualiza la tabla con el contenido del diccionario actual"""
        # Limpiar tabla actual
        for item in self.table.get_children():
            self.table.delete(item)
            
        # Cargar datos del diccionario
        for original, corregida in self.diccionario.items():
            self.table.insert('', 'end', values=(original, corregida))

    def load_json_file(self):
        """Carga el diccionario desde un archivo JSON"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo JSON",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                new_dict = json.load(file)
                
            # Verificar formato
            if not isinstance(new_dict, dict):
                messagebox.showerror("Error", "El archivo no contiene un diccionario válido")
                return
                
            # Actualizar diccionario y tabla
            self.diccionario = new_dict
            self.corrector = CorrectorTexto(self.diccionario)
            self.update_table()
                
            # Actualizar estadísticas
            self.update_statistics()
            self.update_status(f"Diccionario cargado desde {file_path}: {len(self.diccionario)} entradas")
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el archivo: {e}")
            self.update_status(f"Error al cargar archivo: {e}")

    def export_json_file(self):
        """Exporta el diccionario a un archivo JSON"""
        if not self.diccionario:
            messagebox.showwarning("Advertencia", "No hay diccionario para exportar")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="Guardar como JSON",
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(self.diccionario, file, ensure_ascii=False, indent=4)
                
            self.update_status(f"Diccionario exportado a {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar el diccionario: {e}")
            self.update_status(f"Error al exportar: {e}")

    def save_dictionary_to_db(self):
        """Guarda el diccionario actual en ambas bases de datos"""
        if not self.diccionario:
            messagebox.showwarning("Advertencia", "No hay diccionario para guardar")
            return
            
        try:
            exito, mensaje = self.db_manager.guardar_diccionario(self.diccionario)
            
            if exito:
                messagebox.showinfo("Éxito", f"Diccionario guardado:\n{mensaje}")
                self.update_status(mensaje)
            else:
                messagebox.showwarning("Advertencia", f"Problemas al guardar el diccionario:\n{mensaje}")
                self.update_status(f"Advertencia: {mensaje}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar el diccionario: {e}")
            self.update_status(f"Error al guardar: {e}")

    def on_select_word(self, event):
        """Maneja la selección de una entrada en la tabla"""
        selected_items = self.table.selection()
        if not selected_items:
            return
            
        # Obtener datos de la selección
        item = self.table.item(selected_items[0])
        valores = item['values']
        if len(valores) >= 2:
            # Actualizar campos de entrada
            self.original_entry.delete(0, tk.END)
            self.original_entry.insert(0, valores[0])
            
            self.corrected_entry.delete(0, tk.END)
            self.corrected_entry.insert(0, valores[1])
            
            # Determinar si es una frase
            self.is_phrase_var.set(' ' in valores[0])

    def add_update_word(self):
        """Añade o actualiza una entrada en el diccionario"""
        original = self.original_entry.get().strip()
        corrected = self.corrected_entry.get().strip()
        
        if not original or not corrected:
            messagebox.showwarning("Advertencia", "Ambos campos son obligatorios")
            return
            
        # Actualizar diccionario
        self.diccionario[original] = corrected
        
        # Actualizar corrector
        self.corrector = CorrectorTexto(self.diccionario)
        
        # Actualizar tabla (eliminar si existe)
        for item in self.table.get_children():
            if self.table.item(item)['values'][0] == original:
                self.table.delete(item)
                break
                
        # Insertar entrada
        self.table.insert('', 'end', values=(original, corrected))
        
        # Actualizar estadísticas
        self.update_statistics()
        
        # Determinar tipo de entrada para mensaje
        tipo = "frase" if ' ' in original else "palabra"
        self.update_status(f"{tipo} '{original}' añadida/actualizada")
        
        # Limpiar campos
        self.clear_fields()

    def delete_word(self):
        """Elimina una entrada del diccionario"""
        original = self.original_entry.get().strip()
        
        if not original:
            messagebox.showwarning("Advertencia", "Seleccione una entrada para eliminar")
            return
            
        if original not in self.diccionario:
            messagebox.showwarning("Advertencia", f"La entrada '{original}' no existe en el diccionario")
            return
            
        # Eliminar del diccionario
        del self.diccionario[original]
        
        # Actualizar corrector
        self.corrector = CorrectorTexto(self.diccionario)
        
        # Eliminar de la tabla
        for item in self.table.get_children():
            if self.table.item(item)['values'][0] == original:
                self.table.delete(item)
                break
                
        # Actualizar estadísticas
        self.update_statistics()
        
        # Determinar tipo para mensaje
        tipo = "frase" if ' ' in original else "palabra"
        self.update_status(f"{tipo} '{original}' eliminada")
        
        # Limpiar campos
        self.clear_fields()

    def clear_fields(self):
        """Limpia los campos de entrada"""
        self.original_entry.delete(0, tk.END)
        self.corrected_entry.delete(0, tk.END)
        self.is_phrase_var.set(False)

    def load_from_text(self):
        """Carga el diccionario desde el texto ingresado"""
        text = self.text_area.get('1.0', tk.END).strip()
        if not text:
            messagebox.showwarning("Advertencia", "No hay texto para cargar")
            return
            
        # Procesar líneas
        new_dict = {}
        errors = []
        
        for i, line in enumerate(text.split('\n'), 1):
            line = line.strip()
            if not line:
                continue
                
            # Verificar formato correcto (original:corrección)
            parts = line.split(':', 1)
            if len(parts) == 2:
                original = parts[0].strip()
                corrected = parts[1].strip()
                if original and corrected:
                    new_dict[original] = corrected
            else:
                errors.append(f"Línea {i}: '{line}' (formato incorrecto, debe ser 'original:corrección')")
        
        if not new_dict:
            if errors:
                messagebox.showerror("Error", "No se pudo cargar ninguna entrada.\n\nErrores:\n" + "\n".join(errors[:10]) + 
                                    ("\n..." if len(errors) > 10 else ""))
            else:
                messagebox.showwarning("Advertencia", "No se encontraron entradas válidas")
            return
            
        # Confirmar si hay errores
        if errors:
            if not messagebox.askyesno("Advertencia", f"Se encontraron {len(errors)} errores. ¿Desea continuar con las {len(new_dict)} entradas válidas?"):
                return
        
        # Preguntar si se desea reemplazar o añadir
        if self.diccionario:
            respuesta = messagebox.askyesnocancel(
                "Confirmar", 
                "¿Desea reemplazar el diccionario actual?\n\nSí = Reemplazar completamente\nNo = Añadir/actualizar entradas\nCancelar = Cancelar operación"
            )
            
            if respuesta is None:  # Cancelar
                return
            elif respuesta:  # Reemplazar
                self.diccionario = new_dict
            else:  # Añadir/actualizar
                self.diccionario.update(new_dict)
        else:
            # Si no hay diccionario actual, simplemente asignar
            self.diccionario = new_dict
        
        # Actualizar corrector
        self.corrector = CorrectorTexto(self.diccionario)
        
        # Actualizar tabla
        self.update_table()
            
        # Actualizar estadísticas
        self.update_statistics()
        self.update_status(f"Diccionario cargado desde texto: {len(self.diccionario)} entradas")
        
        # Mostrar detalles de errores en área de texto
        if errors:
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert('1.0', "ERRORES ENCONTRADOS:\n\n" + "\n".join(errors) + 
                                "\n\nCORRECCIÓN SUGERIDA:\n\n" + 
                                "\n".join([f"{original}:{corrected}" for original, corrected in self.diccionario.items()]))

    def preview_from_text(self):
        """Muestra una vista previa del diccionario desde el texto ingresado"""
        text = self.text_area.get('1.0', tk.END).strip()
        if not text:
            messagebox.showwarning("Advertencia", "No hay texto para previsualizar")
            return
            
        # Procesar líneas
        preview_dict = {}
        errors = []
        
        for i, line in enumerate(text.split('\n'), 1):
            line = line.strip()
            if not line:
                continue
                
            # Verificar formato correcto (original:corrección)
            parts = line.split(':', 1)
            if len(parts) == 2:
                original = parts[0].strip()
                corrected = parts[1].strip()
                if original and corrected:
                    preview_dict[original] = corrected
            else:
                errors.append(f"Línea {i}: '{line}' (formato incorrecto, debe ser 'original:corrección')")
        
        # Mostrar vista previa
        preview_text = "=== VISTA PREVIA DEL DICCIONARIO ===\n\n"
        
        if preview_dict:
            # Contar tipos
            palabras = sum(1 for k in preview_dict if ' ' not in k)
            frases = sum(1 for k in preview_dict if ' ' in k)
            
            preview_text += f"Entradas válidas: {len(preview_dict)} total ({palabras} palabras, {frases} frases)\n\n"
            
            # Mostrar hasta 20 ejemplos
            preview_text += "Ejemplos:\n"
            for i, (original, corrected) in enumerate(list(preview_dict.items())[:20]):
                tipo = "Frase" if ' ' in original else "Palabra"
                preview_text += f"  • {tipo}: '{original}' → '{corrected}'\n"
                
            if len(preview_dict) > 20:
                preview_text += f"  • ... y {len(preview_dict) - 20} más\n"
        else:
            preview_text += "No se encontraron entradas válidas\n"
            
        if errors:
            preview_text += f"\nErrores encontrados ({len(errors)}):\n"
            for error in errors[:10]:
                preview_text += f"  • {error}\n"
                
            if len(errors) > 10:
                preview_text += f"  • ... y {len(errors) - 10} más\n"
        
        # Mostrar en área de estadísticas y pruebas
        self.test_input.delete('1.0', tk.END)
        self.test_input.insert('1.0', preview_text)
        
        self.update_status(f"Vista previa generada: {len(preview_dict)} entradas válidas, {len(errors)} errores")

    def test_correction(self):
        """Prueba la corrección de texto con el diccionario actual"""
        if not self.diccionario:
            messagebox.showwarning("Advertencia", "No hay diccionario cargado")
            return
            
        original_text = self.test_input.get('1.0', tk.END).strip()
        if not original_text:
            messagebox.showwarning("Advertencia", "No hay texto para corregir")
            return
            
        # Realizar corrección
        corrected_text = self.corrector.corregir_texto(original_text)
        
        # Mostrar resultado
        self.test_output.delete('1.0', tk.END)
        self.test_output.insert('1.0', corrected_text)
        
        # Identificar cambios realizados
        if original_text == corrected_text:
            self.update_status("No se realizaron correcciones")
        else:
            # Contar aproximadamente cuántas correcciones se hicieron
            palabras_originales = original_text.split()
            palabras_corregidas = corrected_text.split()
            
            if len(palabras_originales) == len(palabras_corregidas):
                count = sum(1 for a, b in zip(palabras_originales, palabras_corregidas) if a != b)
                self.update_status(f"Corrección aplicada: {count} cambios")
            else:
                self.update_status("Corrección aplicada")

    def update_statistics(self):
        """Actualiza las estadísticas del diccionario"""
        if not self.diccionario:
            self.stats_label.config(text="Diccionario no cargado")
            return
            
        # Contar tipos
        palabras = sum(1 for k in self.diccionario if ' ' not in k)
        frases = sum(1 for k in self.diccionario if ' ' in k)
        
        # Calcular estadísticas
        total_entradas = len(self.diccionario)
        longitud_promedio_original = sum(len(p) for p in self.diccionario.keys()) / total_entradas if total_entradas > 0 else 0
        longitud_promedio_correccion = sum(len(c) for c in self.diccionario.values()) / total_entradas if total_entradas > 0 else 0
        
        stats_text = f"Total de entradas: {total_entradas}\n"
        stats_text += f"Palabras individuales: {palabras}\n"
        stats_text += f"Frases o expresiones: {frases}\n"
        stats_text += f"Longitud promedio del texto original: {longitud_promedio_original:.2f} caracteres\n"
        stats_text += f"Longitud promedio del texto corregido: {longitud_promedio_correccion:.2f} caracteres"
        
        self.stats_label.config(text=stats_text)

    def update_status(self, message):
        """Actualiza la barra de estado"""
        self.status_bar.config(text=message)
        
    def __del__(self):
        """Cierra las conexiones al cerrar la aplicación"""
        if hasattr(self, 'db_manager'):
            self.db_manager.cerrar_conexiones()

# Función principal
if __name__ == "__main__":
    # Verificar que están disponibles los módulos necesarios
    try:
        # Asegurarse de que la carpeta actual está en la ruta de búsqueda
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            
        # Intentar importar módulos
        from diccionario_utils import CorrectorTexto
        from db_manager import GestorDB
        
        # Iniciar aplicación
        root = tk.Tk()
        app = DiccionarioApp(root)
        root.mainloop()
    except ImportError as e:
        print(f"Error: No se pudo importar un módulo necesario: {e}")
        print("Asegúrese de que los archivos diccionario_utils.py y db_manager.py estén en el mismo directorio.")
        sys.exit(1)
    except Exception as e:
        print(f"Error al iniciar la aplicación: {e}")
        sys.exit(1)