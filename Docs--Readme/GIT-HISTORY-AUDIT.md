# Auditoría de secretos en historial Git (SCRUM-12)

El código actual puede estar limpio y **aún así** quedar secretos en commits antiguos (`.env`, tokens, contraseñas en `settings.py`). Esto complementa [SECRET-ROTATION.md](./SECRET-ROTATION.md).

## Cuándo ejecutar

- Antes de hacer el repo **público** o entregarlo a un cliente.
- Tras la auditoría inicial de SindyBot (PR #1 en adelante ya sacó secretos del *working tree*).

## 1. Escaneo con herramientas (recomendado primero)

| Herramienta | Uso |
|-------------|-----|
| [Gitleaks](https://github.com/gitleaks/gitleaks) | `gitleaks detect --source . --log-opts="--all"` (redacta en salida) |
| [TruffleHog](https://github.com/trufflesecurity/trufflehog) | `trufflehog git file://. --since-commit HEAD~500` |

Si hay hallazgos: **rotar** las credenciales afectadas (checklist en SECRET-ROTATION) aunque borres el historial.

## 2. Escaneo rápido (local, sin diffs)

**No uses `git log -p`** en terminales compartidas, CI logs ni capturas de pantalla: el patch puede **mostrar secretos** aún presentes en commits viejos. Prefiere **`--oneline`** con `-S` (solo metadatos) o gitleaks.

```bash
git log --all -S "DB_PASSWORD" --oneline | head
git log --all -S "SECRET_KEY" --oneline | head
git log --all -S "HF_TOKEN" --oneline | head
git log --all -S "GEMINI_API_KEY" --oneline | head
git log --all -S "AWS_DB_PASSWORD" --oneline | head
```

Script incluido (bash/Git Bash o `./scripts/audit-git-history.sh` si es ejecutable):

```bash
bash scripts/audit-git-history.sh
```

El script lista **conteos** en historial (`-S`) y **rutas en HEAD** sin volcar líneas con secretos. Patrones amplios (`password=`, `.env`) suelen dar muchos hits históricos (ruido); confirme hallazgos con gitleaks antes de rotar.

- [git-filter-repo](https://github.com/newren/git-filter-repo) o [BFG Repo-Cleaner](https://rtyley.github.io/bfg-repo-cleaner/).
- Tras reescribir historial: **force push** coordinado con el equipo y **rotación obligatoria** de todos los secretos que hayan aparecido en commits.
- No uses `--force` en `main` sin acuerdo explícito.

## 4. Verificación post-auditoría

- [ ] Working tree sin secretos (`grep` / gitleaks en HEAD).
- [ ] `.env` fuera del índice (`.gitignore`).
- [ ] Credenciales rotadas en proveedores (Google AI, HF, MySQL, Django `SECRET_KEY`).
- [ ] Documentar fecha de auditoría en Jira **SCRUM-12**.

# Desarrollado por: hcastro
