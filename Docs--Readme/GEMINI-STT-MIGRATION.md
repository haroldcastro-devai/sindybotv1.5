# Migración Gemini (IA) + STT sin GPU propia

## Fase A — IA con Gemini (implementada)

La evaluación de auditoría usa `mod_bot/l_process/llm_client.py` (**solo Google Gemini**; no hay fallback Ollama).

### Configuración `.env`

```env
GEMINI_API_KEY=tu_clave
GEMINI_MODEL=gemini-2.0-flash
```

Sin `GEMINI_API_KEY` la auditoría falla con un error explícito.

### Dependencia

```bash
pip install -r mod_bot/requirements-llm.txt
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

Variable: `STT_PROVIDER=whisperx|faster_whisper|google` (default: `whisperx`)

Punto de extensión: `mod_bot/l_process/stt_provider.py` — usado por `diariza.py` y `unified_processing.py`.

Proveedores `faster_whisper` y `google` aún no implementados; el código devuelve error claro si se seleccionan.

### Tareas sugeridas (Jira)

1. Implementar `faster_whisper` para pruebas en VPS sin GPU.
2. Prototipo Google STT v2 con diarización.
3. Pruebas de regresión con audios de referencia.

---

## Desarrollo en PC bajo recursos

- Editar Django y `llm_client` en local: **sin GPU**.
- Probar auditoría completa: Gemini en cloud + STT whisperx en VM con GPU o Fase B.

# Desarrollado por: hcastro
