# Documentación SindyBot v1.5

**Documento canónico de instalación y operación:** [README.md](../README.md) (raíz del repo).

## IA y audio

| Documento | Contenido |
|-----------|-----------|
| [IA-STT-ARQUITECTURA.md](./IA-STT-ARQUITECTURA.md) | **Gemini (LLM)** vs **STT** (WhisperX / alternativas); no confundir productos Google |
| [GEMINI-STT-MIGRATION.md](./GEMINI-STT-MIGRATION.md) | Configuración detallada Fase A (Gemini) y Fase B (STT) |

## Seguridad y despliegue

| Documento | Contenido |
|-----------|-----------|
| [GIT-HISTORY-AUDIT.md](./GIT-HISTORY-AUDIT.md) | Secretos en historial Git (SCRUM-12) |
| [SECRET-ROTATION.md](./SECRET-ROTATION.md) | Rotación de credenciales |
| [req-envsbot.yaml](./req-envsbot.yaml) | Entorno Conda ML (WhisperX; incluye `faster-whisper` solo si usa Fase B) |

## Módulo de procesamiento

| Documento | Contenido |
|-----------|-----------|
| [mod_bot/readme.md](../mod_bot/readme.md) | Flujo `mod_bot`, `stt_provider`, diariza |

## Scripts útiles (raíz `scripts/`)

| Script | Uso |
|--------|-----|
| `smoke_gemini.py` | Prueba `GEMINI_API_KEY` |
| `verify-django-deploy-check.sh` / `.ps1` | `manage.py check --deploy` |
| `verify_stt_provider_wiring.py` | Comprueba cableado STT → WhisperX vía `stt_provider` (CI) |
| `stt_faster_whisper_regression.py` | Solo si `STT_PROVIDER=faster_whisper` (Fase B) |
| `stt_google_smoke.py` | Solo si `STT_PROVIDER=google` (prototipo) |

## Árbol de directorios

El archivo [estructura_directorios.txt](../estructura_directorios.txt) es un **snapshot histórico** (no se regenera en cada release). Para la estructura lógica actual, use la sección **Estructura de Directorios** del README principal.

# Desarrollado por: hcastro
