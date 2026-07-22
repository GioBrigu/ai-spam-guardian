"""
Repository per la tabella emails: salva e legge i risultati delle classificazioni.
"""

import sqlite3
from datetime import datetime, timezone


def salva_classificazione(connessione: sqlite3.Connection, email: dict, risultato: dict) -> None:
    '''Salva la classificazione di una email (aggiorna se già presente).'''
    connessione.execute('''
        INSERT INTO emails (id, mittente, oggetto, anteprima_corpo, data_ricezione,
                             categoria, confidenza, motivazione, data_classificazione)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            categoria = excluded.categoria,
            confidenza = excluded.confidenza,
            motivazione = excluded.motivazione,
            data_classificazione = excluded.data_classificazione
    ''', (
        email['id'],
        email['from']['emailAddress']['address'],
        email['subject'],
        email['bodyPreview'],
        email['receivedDateTime'],
        risultato['categoria'],
        risultato['confidenza'],
        risultato['motivazione'],
        datetime.now(timezone.utc).isoformat(),
    ))
    connessione.commit()


def email_gia_classificata(connessione: sqlite3.Connection, email_id: str) -> bool:
    '''Controlla se un'email è già stata classificata in precedenza.'''
    cursore = connessione.execute('SELECT 1 FROM emails WHERE id = ?', (email_id,))
    return cursore.fetchone() is not None


def registra_azione(connessione: sqlite3.Connection, email_id: str, azione: str, esito: str) -> None:
    '''Registra nel log un'azione automatica eseguita su un'email.'''
    connessione.execute('''
        INSERT INTO azioni_log (email_id, azione, esito, data_azione)
        VALUES (?, ?, ?, ?)
    ''', (email_id, azione, esito, datetime.now(timezone.utc).isoformat()))
    connessione.commit()