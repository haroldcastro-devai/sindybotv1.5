# Ejecuta manage.py check y check --deploy (SCRUM-32 / review PR #17).
$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

$env:USE_SQLITE_DEMO = 'True'
if (-not $env:SECRET_KEY) { $env:SECRET_KEY = 'ci-check-only-not-for-production' }
$env:DEBUG = 'False'

Write-Host '== manage.py check (SQLite demo) =='
python manage.py check

$env:DJANGO_USE_HTTPS = 'True'
$env:TRUST_X_FORWARDED_PROTO = 'True'
$env:CSRF_TRUSTED_ORIGINS = 'https://example.com'
$env:ALLOWED_HOSTS = 'example.com'

Write-Host '== manage.py check --deploy (HTTPS + proxy) =='
python manage.py check --deploy

Write-Host 'OK: check y check --deploy completados.'

# Desarrollado por: hcastro
