# Migración Gemini (IA) + STT sin GPU propia

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

## Fase B — STT sin WhisperX en GPU (plan)

| Proveedor | Coste | GPU propia | Diarización |
|-----------|-------|------------|-------------|
| `whisperx` (actual) | Infra | Sí | Sí (PyAnnote) |
| `faster_whisper` CPU | Bajo | No (lento) | Limitada (`SPEAKER_00`) |
| Google Cloud Speech-to-Text | Por minuto | No | Opcional API |

Variable: `STT_PROVIDER=whisperx|faster_whisper|google` (default: `whisperx`)

Punto de extensión: `mod_bot/l_process/stt_provider.py` — usado por `diariza.py` y `unified_processing.py`.

### faster_whisper (SCRUM-34 — implementado)

```bash
pip install -r mod_bot/requirements-stt-cpu.txt
# .env
STT_PROVIDER=faster_whisper
FASTER_WHISPER_MODEL=small
FASTER_WHISPER_DEVICE=cpu
FASTER_WHISPER_COMPUTE_TYPE=int8
```

Regresión con hasta 3 audios locales (no versionados):

```bash
python scripts/stt_faster_whisper_regression.py audio1.mp3 audio2.gsm audio3.wav
```

Proveedor `google` aún no implementado; error explícito si se selecciona.

### Tareas sugeridas (Jira)

1. ~~Implementar `faster_whisper` para pruebas en VPS sin GPU.~~ (SCRUM-34)
2. Prototipo Google STT v2 con diarización.
3. Pruebas de regresión con audios de referencia (script anterior + pipeline completo).

---

## Desarrollo en PC bajo recursos

- Editar Django y `llm_client` en local: **sin GPU**.
- Probar auditoría completa: Gemini en cloud + STT whisperx en VM con GPU o Fase B.

# Desarrollado por: hcastro
