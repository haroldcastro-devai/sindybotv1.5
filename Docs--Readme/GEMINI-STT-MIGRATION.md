# Migración Gemini (IA) + STT sin GPU propia

## Fase A — IA con Gemini (implementada)

La evaluación de auditoría usa `mod_bot/l_process/llm_client.py`.

### Configuración `.env`

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=tu_clave
GEMINI_MODEL=gemini-2.0-flash
```

Fallback local (requiere Ollama + GPU/RAM):

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:14b-instruct-q6_K
```

### Dependencia

```bash
pip install google-generativeai
```

### Archivos que llaman al LLM

- `mod_bot/l_process/call_evaluation.py`
- `mod_bot/diariza.py`
- `mod_bot/l_process/unified_processing.py`

---

## Fase B — STT sin WhisperX en GPU (plan)

| Proveedor | Coste | GPU propia | Diarización |
|-----------|-------|------------|-------------|
| `whisperx` (actual) | Infra | Sí | Sí (PyAnnote) |
| `faster_whisper` CPU | Bajo | No (lento) | Limitada |
| Google Cloud Speech-to-Text | Por minuto | No | Opcional API |
| Gemini multimodal (audio) | Por token | No | Cambia diseño |

Variable: `STT_PROVIDER=whisperx|faster_whisper|google`

Punto de extensión: `mod_bot/l_process/stt_provider.py`

### Tareas sugeridas (Jira)

1. Implementar `faster_whisper` para pruebas en VPS sin GPU.
2. Prototipo Google STT v2 con diarización.
3. Sustituir imports directos a `procesar_audio` en `diariza.py` / `unified_processing.py` por `stt_provider`.
4. Pruebas de regresión con 3 audios de referencia en `back/audio-text/`.

---

## Desarrollo del código (PC bajo recursos)

- Editar Django y `llm_client` en local: **sin GPU**.
- Probar auditoría completa: VPS + `LLM_PROVIDER=gemini` y STT en cloud o VM GPU puntual.
