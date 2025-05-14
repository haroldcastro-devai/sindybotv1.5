# Documentación de Datos Base de SINDYBOT

## Descripción General de `\mod_bot\data\raw\`

Esta carpeta contiene los archivos JSON fundamentales que constituyen la base de conocimiento para el sistema de auditoría de SINDYBOT. Estos archivos definen las reglas, criterios, tarifas y guiones contra los cuales se evalúan las llamadas telefónicas durante el proceso de auditoría automatizada.

## Archivos JSON Principales

La carpeta contiene dos archivos JSON principales:

1. **guionV2.json**: Define los guiones de venta oficiales para cada producto y gasera
2. **tarifasV2.json**: Establece los valores oficiales de tarifas, indemnizaciones y coberturas

Estos archivos trabajan en conjunto para proporcionar el marco de referencia utilizado por el sistema para evaluar la adherencia a los guiones y la correcta mención de tarifas y coberturas durante las llamadas de ventas.

## Arquitectura de Datos

### 1. Estructura del archivo `guionV2.json`

Este archivo contiene los guiones estructurados que los asesores deben seguir durante las llamadas de venta. La estructura jerárquica es:

```json
{
  "NOMBRE_PRODUCTO": {
    "NOMBRE_GASERA": {
      "introduccion": "Texto que debe usar el asesor para la introducción...",
      "presentacion": "Texto para la presentación del producto...",
      "validacion_cliente": "Texto para validar datos del cliente...",
      "explicacion_beneficios": "Texto para explicar beneficios...",
      "manejo_objeciones": {
        "precio": "Respuesta a objeción de precio...",
        "interes": "Respuesta a objeción de falta de interés...",
        "tiempo": "Respuesta a objeción de falta de tiempo..."
      },
      "cierre": "Texto para el cierre de la venta...",
      "habeas_data": "Texto legal para habeas data...",
      "despedida": "Texto de despedida..."
    }
  }
}
```

**Características clave:**

- **Multinivel**: Organizado por producto y gasera, permitiendo guiones específicos para cada combinación
- **Segmentado por etapas**: Divide el guion en secciones lógicas que corresponden al flujo natural de una llamada de venta
- **Manejo de objeciones**: Incluye respuestas estándar para las objeciones más comunes
- **Textos legales**: Contiene formulaciones específicas para cumplimiento normativo

### 2. Estructura del archivo `tarifasV2.json`

Este archivo define los valores monetarios oficiales para cada producto, incluyendo:

```json
{
  "NOMBRE_PRODUCTO": {
    "NOMBRE_GASERA": {
      "tarifa": 9999,
      "indemnizacion": 9999999,
      "cobertura": {
        "vida": 5000000,
        "accidental": 10000000,
        "hospitalario": 1000000
      },
      "beneficios_adicionales": [
        "Asistencia jurídica",
        "Asistencia funeraria",
        "Orientación médica telefónica"
      ],
      "edad_minima": 18,
      "edad_maxima": 65,
      "periodo_carencia": 30,
      "vigencia": "12 meses"
    }
  }
}
```

**Características clave:**

- **Valores numéricos precisos**: Define exactamente las tarifas y montos que deben mencionarse
- **Múltiples niveles de cobertura**: Detalla los diferentes tipos de coberturas y sus valores
- **Restricciones de elegibilidad**: Define parámetros como edades mínimas y máximas
- **Información temporal**: Incluye períodos de carencia y vigencia

## Lógica de Uso en el Sistema

Estos archivos JSON son utilizados por SINDYBOT de la siguiente manera:

1. **Durante la evaluación de llamadas**:
   - El sistema extrae la gasera y el producto mencionados en la llamada
   - Carga los datos correspondientes de ambos archivos JSON
   - Compara el discurso del asesor con el guion establecido
   - Verifica que los valores monetarios mencionados coincidan con los oficiales

2. **Criterios de calificación**:
   - Se otorgan puntos por adherencia al guion (correspondencia con secciones del `guionV2.json`)
   - Se penaliza si los montos mencionados no coinciden con los de `tarifasV2.json`
   - Se verifica que las objeciones sean manejadas según las respuestas estándar definidas

3. **Generación del prompt para IA**:
   - Los datos de estos archivos se incluyen en el contexto enviado al modelo de IA
   - Permiten que el modelo tenga los valores de referencia para su análisis

## Migración a Base de Datos

Estos archivos JSON pueden ser utilizados para crear y poblar una base de datos relacional mediante el siguiente esquema:

### Esquema de Base de Datos Propuesto

```sql
-- Tabla de Productos
CREATE TABLE Productos (
    ProductoID INT PRIMARY KEY AUTO_INCREMENT,
    NombreProducto VARCHAR(100) NOT NULL,
    Descripcion TEXT,
    FechaCreacion DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Gaseras
CREATE TABLE Gaseras (
    GaseraID INT PRIMARY KEY AUTO_INCREMENT,
    NombreGasera VARCHAR(100) NOT NULL,
    CodigoGasera VARCHAR(20),
    Activa BOOLEAN DEFAULT TRUE
);

-- Tabla de Tarifas
CREATE TABLE Tarifas (
    TarifaID INT PRIMARY KEY AUTO_INCREMENT,
    ProductoID INT,
    GaseraID INT,
    ValorTarifa DECIMAL(10,2) NOT NULL,
    Indemnizacion DECIMAL(12,2),
    EdadMinima INT,
    EdadMaxima INT,
    PeriodoCarencia INT,
    Vigencia VARCHAR(50),
    FechaActualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID),
    FOREIGN KEY (GaseraID) REFERENCES Gaseras(GaseraID)
);

-- Tabla de Coberturas
CREATE TABLE Coberturas (
    CoberturaID INT PRIMARY KEY AUTO_INCREMENT,
    TarifaID INT,
    TipoCobertura VARCHAR(100) NOT NULL,
    ValorCobertura DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (TarifaID) REFERENCES Tarifas(TarifaID)
);

-- Tabla de Beneficios Adicionales
CREATE TABLE BeneficiosAdicionales (
    BeneficioID INT PRIMARY KEY AUTO_INCREMENT,
    TarifaID INT,
    NombreBeneficio VARCHAR(100) NOT NULL,
    Descripcion TEXT,
    FOREIGN KEY (TarifaID) REFERENCES Tarifas(TarifaID)
);

-- Tabla de Secciones de Guion
CREATE TABLE SeccionesGuion (
    SeccionID INT PRIMARY KEY AUTO_INCREMENT,
    NombreSeccion VARCHAR(100) NOT NULL,
    Descripcion TEXT
);

-- Tabla de Guiones
CREATE TABLE Guiones (
    GuionID INT PRIMARY KEY AUTO_INCREMENT,
    ProductoID INT,
    GaseraID INT,
    SeccionID INT,
    TextoGuion TEXT NOT NULL,
    VersionGuion VARCHAR(20),
    FechaActualizacion DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID),
    FOREIGN KEY (GaseraID) REFERENCES Gaseras(GaseraID),
    FOREIGN KEY (SeccionID) REFERENCES SeccionesGuion(SeccionID)
);

-- Tabla de Objeciones
CREATE TABLE Objeciones (
    ObjecionID INT PRIMARY KEY AUTO_INCREMENT,
    TipoObjecion VARCHAR(100) NOT NULL,
    Descripcion TEXT
);

-- Tabla de Respuestas a Objeciones
CREATE TABLE RespuestasObjeciones (
    RespuestaID INT PRIMARY KEY AUTO_INCREMENT,
    ObjecionID INT,
    ProductoID INT,
    GaseraID INT,
    TextoRespuesta TEXT NOT NULL,
    FOREIGN KEY (ObjecionID) REFERENCES Objeciones(ObjecionID),
    FOREIGN KEY (ProductoID) REFERENCES Productos(ProductoID),
    FOREIGN KEY (GaseraID) REFERENCES Gaseras(GaseraID)
);
```

### Proceso de Migración

Para convertir los archivos JSON a este esquema de base de datos:

1. **Script de conversión**:
   ```python
   import json
   import mysql.connector
   from datetime import datetime

   # Conexión a la BD
   db_connection = mysql.connector.connect(
       host="localhost",
       user="usuario",
       password="contraseña",
       database="sindybot_db"
   )
   cursor = db_connection.cursor()

   # Cargar archivos JSON
   with open('guionV2.json', 'r', encoding='utf-8') as file:
       guiones_data = json.load(file)
       
   with open('tarifasV2.json', 'r', encoding='utf-8') as file:
       tarifas_data = json.load(file)

   # Poblar tablas
   # 1. Insertar productos y gaseras
   for producto in guiones_data.keys():
       cursor.execute("INSERT INTO Productos (NombreProducto) VALUES (%s)", (producto,))
       producto_id = cursor.lastrowid
       
       for gasera in guiones_data[producto].keys():
           cursor.execute("INSERT INTO Gaseras (NombreGasera) VALUES (%s)", (gasera,))
           gasera_id = cursor.lastrowid
           
           # 2. Insertar tarifas
           if producto in tarifas_data and gasera in tarifas_data[producto]:
               tarifa_info = tarifas_data[producto][gasera]
               cursor.execute("""
                   INSERT INTO Tarifas 
                   (ProductoID, GaseraID, ValorTarifa, Indemnizacion, EdadMinima, EdadMaxima, PeriodoCarencia, Vigencia) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               """, (
                   producto_id, 
                   gasera_id, 
                   tarifa_info.get('tarifa'), 
                   tarifa_info.get('indemnizacion'),
                   tarifa_info.get('edad_minima'),
                   tarifa_info.get('edad_maxima'),
                   tarifa_info.get('periodo_carencia'),
                   tarifa_info.get('vigencia')
               ))
               tarifa_id = cursor.lastrowid
               
               # 3. Insertar coberturas
               if 'cobertura' in tarifa_info:
                   for tipo_cobertura, valor in tarifa_info['cobertura'].items():
                       cursor.execute("""
                           INSERT INTO Coberturas (TarifaID, TipoCobertura, ValorCobertura)
                           VALUES (%s, %s, %s)
                       """, (tarifa_id, tipo_cobertura, valor))
               
               # 4. Insertar beneficios adicionales
               if 'beneficios_adicionales' in tarifa_info:
                   for beneficio in tarifa_info['beneficios_adicionales']:
                       cursor.execute("""
                           INSERT INTO BeneficiosAdicionales (TarifaID, NombreBeneficio)
                           VALUES (%s, %s)
                       """, (tarifa_id, beneficio))
           
           # 5. Insertar secciones de guion
           guion_info = guiones_data[producto][gasera]
           for seccion, texto in guion_info.items():
               if seccion != 'manejo_objeciones':
                   # Obtener o crear sección
                   cursor.execute("SELECT SeccionID FROM SeccionesGuion WHERE NombreSeccion = %s", (seccion,))
                   seccion_result = cursor.fetchone()
                   
                   if seccion_result:
                       seccion_id = seccion_result[0]
                   else:
                       cursor.execute("INSERT INTO SeccionesGuion (NombreSeccion) VALUES (%s)", (seccion,))
                       seccion_id = cursor.lastrowid
                   
                   # Insertar guion
                   cursor.execute("""
                       INSERT INTO Guiones (ProductoID, GaseraID, SeccionID, TextoGuion)
                       VALUES (%s, %s, %s, %s)
                   """, (producto_id, gasera_id, seccion_id, texto))
               else:
                   # Manejo de objeciones
                   for tipo_objecion, respuesta in texto.items():
                       # Obtener o crear objeción
                       cursor.execute("SELECT ObjecionID FROM Objeciones WHERE TipoObjecion = %s", (tipo_objecion,))
                       objecion_result = cursor.fetchone()
                       
                       if objecion_result:
                           objecion_id = objecion_result[0]
                       else:
                           cursor.execute("INSERT INTO Objeciones (TipoObjecion) VALUES (%s)", (tipo_objecion,))
                           objecion_id = cursor.lastrowid
                       
                       # Insertar respuesta a objeción
                       cursor.execute("""
                           INSERT INTO RespuestasObjeciones (ObjecionID, ProductoID, GaseraID, TextoRespuesta)
                           VALUES (%s, %s, %s, %s)
                       """, (objecion_id, producto_id, gasera_id, respuesta))
   
   # Confirmar cambios
   db_connection.commit()
   
   # Cerrar conexión
   cursor.close()
   db_connection.close()
   ```

2. **Ventajas de la migración a base de datos**:
   - **Consultas más eficientes**: Permite filtrar y buscar información con mayor rapidez
   - **Integridad referencial**: Garantiza la consistencia de los datos mediante claves foráneas
   - **Historial de cambios**: Facilita el seguimiento de modificaciones con campos de fecha
   - **Escalabilidad**: Soporta mejor el crecimiento de productos, gaseras y versiones
   - **Seguridad**: Permite implementar controles de acceso detallados por tabla o campo

3. **Consideraciones para la implementación**:
   - **Versión de prueba**: Mantener los archivos JSON como respaldo durante la migración
   - **Validación cruzada**: Verificar que ambas fuentes de datos generen los mismos resultados
   - **Actualización gradual**: Modificar los módulos de SINDYBOT para usar la BD en lugar de JSON
   - **Copia de seguridad**: Implementar respaldos automáticos de la base de datos

## Mantenimiento y Actualización

Tanto los archivos JSON como la base de datos relacional propuesta requieren un mantenimiento regular:

### Para archivos JSON:

1. **Control de versiones**: Utilizar algún sistema de control de versiones para rastrear cambios
2. **Validación de formato**: Verificar la sintaxis JSON antes de implementar cambios
3. **Copia de seguridad**: Mantener respaldos de versiones anteriores

### Para base de datos:

1. **Procedimientos almacenados**: Implementar funciones para añadir/actualizar productos y tarifas
2. **Interfaz administrativa**: Desarrollar un panel para que administradores puedan modificar datos
3. **Auditoría de cambios**: Registrar qué usuario realizó cada modificación y cuándo

## Conclusión

Los archivos JSON en `\mod_bot\data\raw\` representan el núcleo de conocimiento para las evaluaciones de SINDYBOT. Su estructura facilita tanto el uso directo como la migración a una base de datos relacional para mayor escalabilidad y rendimiento.

La migración a una base de datos ofrece ventajas significativas para proyectos en crecimiento, mientras que el formato JSON proporciona simplicidad y portabilidad para configuraciones iniciales o más pequeñas.

---

*Nota: Esta documentación está diseñada para facilitar la comprensión y transferencia del proyecto SINDYBOT. Para cualquier información adicional o aclaración, por favor consultar al equipo de desarrollo.*
