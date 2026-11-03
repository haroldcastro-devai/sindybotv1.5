# Rotación de secretos expuestos en Git

Los valores que antes estaban en código o en commits **siguen en el historial de Git**. Cambiar el código no los invalida. Rota cada credencial **antes** de mergear a producción o compartir el repo.

## Checklist

| Secreto | Acción |
|---------|--------|
| `SECRET_KEY` (Django) | Generar nueva clave (`django.core.management.utils.get_random_secret_key()`), actualizar `.env`, invalidar sesiones existentes. |
| Contraseña MySQL (`DB_PASSWORD`, usuario `adminsbot`) | `ALTER USER` en MySQL + actualizar `.env` y Docker. |
| Token Hugging Face (ex filtrado en `audio_processing.py`) | Revocar en [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens), crear token nuevo, `HF_TOKEN` en `.env`. |
| Credenciales AWS/MySQL comentadas (histórico en `settings.py`) | Rotar en AWS/RDS si esas credenciales fueron reales; no reintroducir en el repo. |

## Opcional: limpiar historial

Si el repo fue o será público, valora `git filter-repo` o BFG para eliminar secretos del historial y **forzar rotación** de todos los valores afectados. Procedimiento detallado: [GIT-HISTORY-AUDIT.md](./GIT-HISTORY-AUDIT.md) (SCRUM-12).

## Verificación

- `grep` en el working tree sin contraseñas ni tokens.
- Nuevo `.env` local nunca commiteado (`.gitignore`).

# Desarrollado por: hcastro
