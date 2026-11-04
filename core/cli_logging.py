"""Logging mínimo para scripts CLI antes de cargar Django."""
import logging
import os

_CONFIGURED = False


def configure_cli_logging(default_level: str = "WARNING") -> None:
    """Consola para manage.py / start_server.py; nivel vía LOG_LEVEL en entorno."""
    global _CONFIGURED
    if _CONFIGURED or logging.root.handlers:
        return
    level_name = os.environ.get("LOG_LEVEL", default_level).upper()
    level = getattr(logging, level_name, logging.WARNING)
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
    )
    _CONFIGURED = True

# Desarrollado por: hcastro
