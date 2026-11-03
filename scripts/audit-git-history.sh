#!/usr/bin/env bash
# Escaneo ligero de patrones sensibles en historial Git (SCRUM-12).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PATTERNS=(
  "DB_PASSWORD"
  "SECRET_KEY"
  "HF_TOKEN"
  "GEMINI_API_KEY"
  "AWS_DB_PASSWORD"
  "mysql.connector.connect"
  "password="
  ".env"
)

echo "=== SindyBot — audit-git-history (HEAD working tree + log -S) ==="
for pat in "${PATTERNS[@]}"; do
  count=$(git log --all -S "$pat" --oneline 2>/dev/null | wc -l | tr -d ' ')
  echo "[$pat] commits touching pattern (-S): $count"
  if [ "$count" != "0" ] && [ "$count" -le 15 ]; then
    git log --all -S "$pat" --oneline 2>/dev/null | head -5
  fi
done

echo ""
echo "Ejecute gitleaks/trufflehog para un informe completo (ver Docs--Readme/GIT-HISTORY-AUDIT.md)."

# Desarrollado por: hcastro
