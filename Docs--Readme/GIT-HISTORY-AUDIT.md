# Auditoría de secretos en historial Git (SCRUM-12)

El código actual puede estar limpio y **aún así** quedar secretos en commits antiguos (`.env`, tokens, contraseñas en `settings.py`). Esto complementa [SECRET-ROTATION.md](./SECRET-ROTATION.md).

## Cuándo ejecutar

- Antes de hacer el repo **público** o entregarlo a un cliente.
- Tras la auditoría inicial de SindyBot (PR #1 en adelante ya sacó secretos del *working tree*).

## 1. Escaneo rápido (local)

Desde la raíz del repo:

```bash
# Patrones habituales en todo el historial
git log -p --all -S "DB_PASSWORD" --oneline | head
git log -p --all -S "SECRET_KEY" --oneline | head
git log -p --all -S "HF_TOKEN" --oneline | head
git log -p --all -S "GEMINI_API_KEY" --oneline | head
git log -p --all -S "AWS_DB_PASSWORD" --oneline | head
```

Script incluido (bash/Git Bash):

```bash
bash scripts/audit-git-history.sh
```

## 2. Escaneo con herramientas (recomendado)

| Herramienta | Uso |
|-------------|-----|
| [Gitleaks](https://github.com/gitleaks/gitleaks) | `gitleaks detect --source . --log-opts="--all"` |
| [TruffleHog](https://github.com/trufflesecurity/trufflehog) | `trufflehog git file://. --since-commit HEAD~500` |

Si hay hallazgos: **rotar** las credenciales afectadas (checklist en SECRET-ROTATION) aunque borres el historial.

## 3. Limpiar historial (solo si es imprescindible)

- [git-filter-repo](https://github.com/newren/git-filter-repo) o [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/).
- Tras reescribir historial: **force push** coordinado con el equipo y **rotación obligatoria** de todos los secretos que hayan aparecido en commits.
- No uses `--force` en `main` sin acuerdo explícito.

## 4. Verificación post-auditoría

- [ ] Working tree sin secretos (`grep` / gitleaks en HEAD).
- [ ] `.env` fuera del índice (`.gitignore`).
- [ ] Credenciales rotadas en proveedores (Google AI, HF, MySQL, Django `SECRET_KEY`).
- [ ] Documentar fecha de auditoría en Jira **SCRUM-12**.

# Desarrollado por: hcastro
