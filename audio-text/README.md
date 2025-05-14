# Directorio `audio-text`

Este directorio contiene los archivos de texto generados por la conversión de audio a texto del sistema SBOT.

## Estructura de directorios

- **log_audio_to_text/**: Contiene las transcripciones individuales de cada archivo de audio procesado.
- **Log_sales_audito/**: Contiene los resultados de la auditoría para cada archivo procesado, con sufijo "_auditoria.txt".
- **uni_files_audito/**: Contiene las transcripciones unificadas cuando un audio está dividido en múltiples partes.

## Formato de los archivos

- Los archivos de transcripción tienen el formato `[nombre_original].[extensión].txt`
- Los archivos de auditoría tienen el formato `[nombre_original].[extensión]_auditoria.txt`
- Los archivos unificados tienen el formato `[nombre_sin_parte].gsm_UNIFICADO`

## Notas importantes

- Esta estructura de directorios es compatible con entornos Linux y Docker.
- Todas las rutas en el código son relativas, lo que garantiza la portabilidad del sistema.
- No se debe modificar la estructura de directorios, ya que esto podría afectar el funcionamiento del sistema.
