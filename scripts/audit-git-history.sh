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

NOISY_PATTERNS=("password=" ".env")

is_noisy() {
  local p="$1"
  for n in "${NOISY_PATTERNS[@]}"; do
    if [ "$p" = "$n" ]; then
      return 0
    fi
  done
  return 1
}

echo "=== SindyBot — audit-git-history ==="
echo ""
echo "--- HEAD (solo rutas; no se imprime contenido de archivos) ---"
for pat in "${PATTERNS[@]}"; do
  files=$(git grep -l "$pat" HEAD 2>/dev/null || true)
  if [ -n "$files" ]; then
    n=$(echo "$files" | wc -l | tr -d ' ')
    echo "[$pat] $n archivo(s) en HEAD (revisar; puede ser .env.example u otros):"
    echo "$files" | head -8 | sed 's/^/  /'
  fi
done

echo ""
echo "--- Historial (git log -S, sin -p) ---"
for pat in "${PATTERNS[@]}"; do
  count=$(git log --all -S "$pat" --oneline 2>/dev/null | wc -l | tr -d ' ')
  suffix=""
  if is_noisy "$pat"; then
    suffix=" (patrón ruidoso; confirmar con gitleaks)"
  fi
  echo "[$pat] commits (-S): $count$suffix"
  if [ "$count" != "0" ] && [ "$count" -le 15 ] && ! is_noisy "$pat"; then
    git log --all -S "$pat" --oneline 2>/dev/null | head -5 | sed 's/^/  /'
  fi
done

echo ""
echo "Informe completo: gitleaks detect --source . --log-opts=\"--all\""
echo "Ver Docs--Readme/GIT-HISTORY-AUDIT.md"

# Desarrollado por: hcastro
