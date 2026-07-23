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


def leggi_email_classificate(connessione: sqlite3.Connection) -> list[dict]:
    '''Restituisce tutte le email classificate: id, oggetto e categoria assegnata.'''
    cursore = connessione.execute('SELECT id, oggetto, categoria FROM emails ORDER BY data_classificazione DESC')
    colonne = [descrizione[0] for descrizione in cursore.description]
    return [dict(zip(colonne, riga)) for riga in cursore.fetchall()]


def salva_feedback(connessione: sqlite3.Connection, email_id: str, categoria_originale: str, categoria_corretta: str) -> None:
    '''Salva una correzione manuale della categoria di un'email.'''
    connessione.execute('''
        INSERT INTO feedback (email_id, categoria_originale, categoria_corretta, data_correzione)
        VALUES (?, ?, ?, ?)
    ''', (email_id, categoria_originale, categoria_corretta, datetime.now(timezone.utc).isoformat()))
    connessione.commit()


def registra_esecuzione(connessione: sqlite3.Connection, email_lette: int, email_nuove: int, errori: int) -> None:
    '''Registra un riepilogo di una esecuzione della pipeline.'''
    connessione.execute('''
        INSERT INTO esecuzioni_log (data_esecuzione, email_lette, email_nuove, errori)
        VALUES (?, ?, ?, ?)
    ''', (datetime.now(timezone.utc).isoformat(), email_lette, email_nuove, errori))
    connessione.commit()


def leggi_log_esecuzioni(connessione: sqlite3.Connection, limite: int = 20) -> list[dict]:
    '''Restituisce le ultime esecuzioni della pipeline, più recenti prima.'''
    cursore = connessione.execute('''
        SELECT data_esecuzione, email_lette, email_nuove, errori
        FROM esecuzioni_log
        ORDER BY data_esecuzione DESC
        LIMIT ?
    ''', (limite,))
    colonne = [descrizione[0] for descrizione in cursore.description]
    return [dict(zip(colonne, riga)) for riga in cursore.fetchall()]