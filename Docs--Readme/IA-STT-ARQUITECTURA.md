# IA (Gemini) y STT (WhisperX) en SindyBot

SindyBot usa **dos capas de IA distintas**. No confundirlas:

| Capa | Función | Tecnología por defecto | Variable principal |
|------|---------|------------------------|------------------|
| **LLM** | Auditoría de guiones / calificación sobre **texto** | **Google Gemini** | `GEMINI_API_KEY` |
| **STT** | **Audio → transcripción** (+ diarización) | **WhisperX** (GPU) | `STT_PROVIDER=whisperx` |

Gemini **no transcribe** audio. Google Cloud **Speech-to-Text** **no es** Gemini: es otro API de GCP, solo activo con `STT_PROVIDER=google`.

Punto de unión en código: tras el STT, el texto pasa al LLM (`llm_client.py`, `call_evaluation.py`, `diariza.py`).

---

## 1. LLM — Google Gemini (producción)

La evaluación de auditoría usa `mod_bot/l_process/llm_client.py` (**solo Gemini**, SDK **`google-genai`**; sin Ollama).

### Configuración `.env`

```env
GEMINI_API_KEY=tu_clave
GEMINI_MODEL=gemini-3.8-flash
```

Sin `GEMINI_API_KEY` la auditoría falla con un error explícito.

### Dependencia

```bash
pip install -r mod_bot/requirements-llm.txt
```

Paquete: **`google-genai`** (no usar `google-generativeai` legacy).

### Smoke test

```bash
python scripts/smoke_gemini.py
```

Esperado: `Smoke Gemini: OK`. Errores típicos: modelo, cuota, safety filter.

### Archivos que llaman al LLM

- `mod_bot/l_process/call_evaluation.py`
- `mod_bot/diariza.py`
- `mod_bot/l_process/unified_processing.py`

---

## 2. STT — transcripción de audio

### 2.1 Producción recomendada: WhisperX (GPU)

| | |
|--|--|
| **Variable** | `STT_PROVIDER=whisperx` (default en `.env.example`) |
| **Código** | `mod_bot/l_process/audio_processing.py` vía `stt_provider.py` |
| **Requisitos** | GPU NVIDIA, `HF_TOKEN` (PyAnnote), entorno WhisperX |
| **Diarización** | Sí (vendedor / cliente) |

No cambie el default en producción salvo que pruebe alternativas a propósito.

### 2.2 Alternativas sin GPU (Fase B, opcionales)

Implementadas en `mod_bot/l_process/stt_provider.py` (`diariza.py`, `unified_processing.py`).

| `STT_PROVIDER` | Uso | Diarización |
|----------------|-----|-------------|
| `faster_whisper` | VPS / CPU local | Limitada (`SPEAKER_00`) |
| `google` | Prototipo GCP Speech-to-Text | Opcional API (coste/min) |

#### faster_whisper (SCRUM-34)

```bash
pip install -r mod_bot/requirements-stt-cpu.txt
STT_PROVIDER=faster_whisper
FASTER_WHISPER_MODEL=small
FASTER_WHISPER_DEVICE=cpu
FASTER_WHISPER_COMPUTE_TYPE=int8
```

Regresión (hasta 3 audios locales, no versionados):

```bash
python scripts/stt_faster_whisper_regression.py audio1.mp3 audio2.gsm audio3.wav
```

No sustituye multi-hablante en auditoría con roles → mantenga `whisperx` en producción.

#### Google Cloud Speech-to-Text (SCRUM-35, prototipo)

**No es Gemini.** API Speech con cuenta de servicio:

```bash
pip install -r mod_bot/requirements-stt-google.txt
export GOOGLE_APPLICATION_CREDENTIALS=/ruta/sa.json
STT_PROVIDER=google
GOOGLE_SPEECH_LANGUAGE_CODE=es-CO
GOOGLE_SPEECH_ENABLE_DIARIZATION=True
GOOGLE_SPEECH_MIN_SPEAKERS=2
GOOGLE_SPEECH_MAX_SPEAKERS=2
GOOGLE_SPEECH_OPERATION_TIMEOUT=3600
```

- **Coste:** por minuto de audio ([precios](https://cloud.google.com/speech-to-text/pricing)); `GOOGLE_SPEECH_ENABLE_DIARIZATION=False` reduce factura si solo necesita texto.
- **Audio:** normalizado con **ffmpeg** (LINEAR16 16 kHz mono); límite **10 MB** inline.
- **Timeout:** bloquea el worker hasta `GOOGLE_SPEECH_OPERATION_TIMEOUT` segundos.
- **Privacidad:** el audio sale a Google Cloud; requiere DPA/política interna.
- **Smoke:** `python scripts/stt_google_smoke.py ruta/audio.gsm`

### 2.3 Pendiente Jira

- SCRUM-36: regresión / documentación unificada del flujo `stt_provider`.

---

## 3. Desarrollo en PC sin GPU

- Django + **Gemini** (LLM): viable en local con `GEMINI_API_KEY`.
- **STT whisperx:** requiere VM con GPU o usar `faster_whisper` / `google` para pruebas de transcripción.
- Pipeline completo típico: STT en GPU (o alternativa Fase B) + Gemini en cloud para la auditoría.

# Desarrollado por: hcastro
