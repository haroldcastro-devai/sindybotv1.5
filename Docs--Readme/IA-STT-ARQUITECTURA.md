# IA (Gemini) y STT (WhisperX) en SindyBot

Índice general: [INDICE-DOCUMENTACION.md](./INDICE-DOCUMENTACION.md)

| Capa | Función | Default | Variable |
|------|---------|---------|----------|
| **LLM** | Auditoría sobre **texto** | **Gemini** | `GEMINI_API_KEY` |
| **STT** | **Audio → texto + diarización** | **WhisperX** | `STT_PROVIDER=whisperx` |

Gemini **no** transcribe audio. En operación normal **no** se usa `faster_whisper` ni Google Speech; existen en código solo como alternativas documentadas en Fase B.

**Entrada única STT:** `procesar_audio_via_provider()` en `mod_bot/l_process/stt_provider.py`  
Usado por `diariza.py` y `unified_processing.py` (SCRUM-36). Verificación: `python scripts/verify_stt_provider_wiring.py`.

---

## 1. LLM — Gemini

Ver Fase A en [GEMINI-STT-MIGRATION.md](./GEMINI-STT-MIGRATION.md) o README § Gemini. Smoke: `python scripts/smoke_gemini.py`.

---

## 2. STT — WhisperX (producción)

| Paso | Detalle |
|------|---------|
| Variable | `STT_PROVIDER=whisperx` (default en `.env.example`) |
| Código | `audio_processing.py` ← `stt_provider.py` |
| Infra | GPU NVIDIA, `HF_TOKEN`, FFmpeg |
| Entorno | [`req-envsbot.yaml`](./req-envsbot.yaml) (`whisperx`, PyAnnote, PyTorch) |

WhisperX separa hablantes (PyAnnote). Sin este backend la auditoría por roles vendedor/cliente no es fiable.

---

## 3. Otros `STT_PROVIDER` (no estándar)

| Valor | Uso |
|-------|-----|
| `faster_whisper` | Prueba CPU; un solo hablante (`SPEAKER_00`) — **no** equivalente a WhisperX |
| `google` | Prototipo GCP Speech-to-Text (≠ Gemini); coste/min |

Configuración y scripts de regresión: [GEMINI-STT-MIGRATION.md](./GEMINI-STT-MIGRATION.md) (Fase B). No activar en producción SindyBot salvo excepción acordada.

---

## 4. Desarrollo sin GPU local

Edite Django y `llm_client` en cualquier PC. Para audio, use una VM con GPU y `STT_PROVIDER=whisperx`, o consulte Fase B solo para pruebas puntuales.

# Desarrollado por: hcastro
