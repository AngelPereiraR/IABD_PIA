#!/usr/bin/env python3
"""
Script para inicializar los schemas de la base de datos.
Crea las tablas: users, job_offers

Uso:
    python init_db.py
"""
from dotenv import load_dotenv
load_dotenv()

from src.database import Base, DATABASE_URL, init_db_sync

if __name__ == "__main__":
    print(f"Conectando a: {DATABASE_URL[:40]}...")
    print("Tablas a crear:", [t for t in Base.metadata.tables])
    init_db_sync()
