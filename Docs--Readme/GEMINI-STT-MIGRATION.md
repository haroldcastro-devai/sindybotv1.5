# Migración Gemini (IA) + STT sin GPU propia

> Resumen LLM vs STT: [IA-STT-ARQUITECTURA.md](./IA-STT-ARQUITECTURA.md)

## Fase A — IA con Gemini (implementada)

La evaluación de auditoría usa `mod_bot/l_process/llm_client.py` (**solo Google Gemini**, SDK oficial **`google-genai`**; no hay fallback Ollama).

### Configuración `.env`

```env
GEMINI_API_KEY=tu_clave
GEMINI_MODEL=gemini-3.8-flash
```

Sin `GEMINI_API_KEY` la auditoría falla con un error explícito.

### Dependencia

Paquete PyPI: **`google-genai`** (no usar el legacy `google-generativeai`).

```bash
pip install -r mod_bot/requirements-llm.txt
```

### Smoke test (antes de merge / tras cambios en `llm_client`)

Con `.env` configurado:

```bash
python scripts/smoke_gemini.py
```

Esperado: línea `Smoke Gemini: OK` (o respuesta breve). Errores típicos: modelo inexistente, cuota/créditos, bloqueo safety (mensaje en la excepción).

### Archivos que llaman al LLM

- `mod_bot/l_process/call_evaluation.py`
- `mod_bot/diariza.py`
- `mod_bot/l_process/unified_processing.py`

---

## Fase B — STT sin WhisperX en GPU

| Proveedor | Coste | GPU propia | Diarización |
|-----------|-------|------------|-------------|
| `whisperx` (actual) | Infra | Sí | Sí (PyAnnote) |
| `faster_whisper` CPU | Bajo | No (lento) | Limitada (`SPEAKER_00`) |
| Google Cloud Speech-to-Text | Por minuto | No | Opcional API |

Variable: `STT_PROVIDER=whisperx|faster_whisper|google` (default: `whisperx`)

**Punto único de entrada:** `stt_provider.procesar_audio_via_provider` — `diariza.py` y `unified_processing.py` (SCRUM-36).  
Verificación en CI/local: `python scripts/verify_stt_provider_wiring.py`.

### faster_whisper (SCRUM-34 — implementado)

```bash
pip install -r mod_bot/requirements-stt-cpu.txt
STT_PROVIDER=faster_whisper
FASTER_WHISPER_MODEL=small
FASTER_WHISPER_DEVICE=cpu
FASTER_WHISPER_COMPUTE_TYPE=int8
```

```bash
python scripts/stt_faster_whisper_regression.py audio1.mp3 audio2.gsm audio3.wav
```

### Google Cloud Speech-to-Text (SCRUM-35 — prototipo; no es Gemini)

```bash
pip install -r mod_bot/requirements-stt-google.txt
export GOOGLE_APPLICATION_CREDENTIALS=/ruta/sa.json
STT_PROVIDER=google
GOOGLE_SPEECH_LANGUAGE_CODE=es-CO
GOOGLE_SPEECH_ENABLE_DIARIZATION=True
GOOGLE_SPEECH_OPERATION_TIMEOUT=3600
```

Smoke: `python scripts/stt_google_smoke.py ruta/audio.gsm`

### Unificación stt_provider (SCRUM-36 — implementado)

- No importar `procesar_audio` fuera de `stt_provider.py`.
- `analizar_hablantes()` sigue en `audio_processing.py` (funciona con cualquier backend que devuelva `segments`).

---

## Desarrollo en PC bajo recursos

- Editar Django y `llm_client` en local: **sin GPU**.
- STT producción: `whisperx` en VM GPU; alternativas Fase B para pruebas.

# Desarrollado por: hcastro
