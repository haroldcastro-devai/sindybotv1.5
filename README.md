# SBOT - Sistema de Inteligencia Artificial para Auditoría

## Inicio del Servidor

Para iniciar el servidor SBOT con la visualización profesional de logs, utilice cualquiera de los siguientes métodos:

### Método 1: Archivo Batch (Recomendado para Windows)

Simplemente haga doble clic en el archivo:
```
iniciar_servidor.bat
```

### Método 2: Línea de Comandos

Ejecute el siguiente comando desde la terminal:
```
python start_server.py
```

### Modo Demostración (opcional)

Para iniciar el servidor en modo demostración, que simula actividades como procesamiento de archivos:
```
python start_server.py --demo
```

## Características de la Visualización

- **Banner profesional**: Muestra información del sistema al inicio
- **Logs con formato mejorado**: Usa colores e iconos para mejor legibilidad
- **Reducción de ruido**: Agrupa peticiones similares y reduce mensajes repetitivos
- **Resúmenes de actividad**: Proporciona estadísticas periódicas del sistema

## Estructura del Proyecto

- `start_server.py`: Script principal para iniciar el servidor con logs profesionales
- `iniciar_servidor.bat`: Archivo batch para fácil inicio en Windows
- `banner.py`: Configuración del banner de inicio del sistema
- `audio-text/`: Directorio para almacenar archivos de texto convertidos de audio
