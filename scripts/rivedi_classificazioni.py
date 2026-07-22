"""
Legge il database e mostra le email classificate, raggruppate per categoria,
insieme all'azione automatica eseguita su ciascuna.

Uso (dalla root del progetto):
    uv run scripts/rivedi_classificazioni.py
"""

from spam_guardian.db import database

connessione = database.crea_connessione()

cursore = connessione.execute('''
    SELECT e.categoria, e.oggetto, e.confidenza, COALESCE(a.azione, 'non registrata') AS azione
    FROM emails e
    LEFT JOIN azioni_log a ON a.email_id = e.id
    ORDER BY e.categoria, e.confidenza DESC
''')

categoria_corrente = None

for categoria, oggetto, confidenza, azione in cursore:
    if categoria != categoria_corrente:
        categoria_corrente = categoria
        print(f'\n=== {categoria.upper()} ===')

    print(f'  [{confidenza:.2f}] {oggetto}  ->  {azione}')

connessione.close()