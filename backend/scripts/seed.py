"""Crea el superadmin de plataforma y sincroniza el catalogo de permisos.

Uso: python -m scripts.seed
"""
import asyncio
import logging

from app.bootstrap import bootstrap

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    asyncio.run(bootstrap())
    print("Seed completado.")
