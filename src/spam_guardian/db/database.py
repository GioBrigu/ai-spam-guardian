"""
Connessione al database SQLite e creazione dello schema.
"""

import sqlite3

from .. import config


def crea_connessione() -> sqlite3.Connection:
    '''Apre (o crea, se non esiste ancora) il file del database SQLite.'''
    return sqlite3.connect(config.DB_PATH)


def crea_schema(connessione: sqlite3.Connection) -> None:
    '''Crea la tabella emails se non esiste già.'''
    connessione.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id TEXT PRIMARY KEY,
            mittente TEXT NOT NULL,
            oggetto TEXT NOT NULL,
            anteprima_corpo TEXT,
            data_ricezione TEXT NOT NULL,
            categoria TEXT NOT NULL,
            confidenza REAL NOT NULL,
            motivazione TEXT,
            data_classificazione TEXT NOT NULL
        )
    ''')
    connessione.commit()