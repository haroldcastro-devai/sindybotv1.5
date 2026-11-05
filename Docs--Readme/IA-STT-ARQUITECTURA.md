# IA (Gemini) y STT (WhisperX) en SindyBot

Índice general: [INDICE-DOCUMENTACION.md](./INDICE-DOCUMENTACION.md)

| Capa | Función | Default | Variable |
|------|---------|---------|----------|
| **LLM** | Auditoría sobre **texto** | **Gemini** | `GEMINI_API_KEY` |
| **STT** | **Audio → texto** | **WhisperX** | `STT_PROVIDER=whisperx` |

Gemini no transcribe audio. Google **Speech-to-Text** ≠ Gemini (`STT_PROVIDER=google`).

**Entrada única STT:** `procesar_audio_via_provider()` en `mod_bot/l_process/stt_provider.py`  
Usado por `diariza.py` y `unified_processing.py` (SCRUM-36). Verificación: `python scripts/verify_stt_provider_wiring.py`.

---

## 1. LLM — Gemini

Ver sección Fase A en [GEMINI-STT-MIGRATION.md](./GEMINI-STT-MIGRATION.md) o README § Gemini. Smoke: `python scripts/smoke_gemini.py`.

---

## 2. STT — proveedores

| `STT_PROVIDER` | Backend | Notas |
|----------------|---------|--------|
| `whisperx` | `audio_processing.py` | Producción GPU + `HF_TOKEN` |
| `faster_whisper` | `stt_faster_whisper.py` | CPU; diarización limitada |
| `google` | `stt_google.py` | GCP Speech; coste/min |

Detalle de configuración: [GEMINI-STT-MIGRATION.md](./GEMINI-STT-MIGRATION.md) (Fase B). Operación Google STT (privacidad, coste): README *SCRUM-35*.

---

## 3. Desarrollo sin GPU

LLM Gemini en local; STT vía GPU remota o `faster_whisper` / `google` para pruebas.

# Desarrollado por: hcastro
