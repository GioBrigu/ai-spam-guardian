"""
Analizza le correzioni manuali salvate in "feedback" e mostra un riepilogo
delle coppie di categorie più confuse dal modello, con il dettaglio di ogni
correzione.

Uso (dalla root del progetto):
    uv run scripts/analizza_feedback.py
"""

from collections import Counter

from spam_guardian.db import database

connessione = database.crea_connessione()

cursore = connessione.execute('''
    SELECT f.categoria_originale, f.categoria_corretta, e.oggetto, f.data_correzione
    FROM feedback f
    JOIN emails e ON e.id = f.email_id
    ORDER BY f.data_correzione
''')

correzioni = cursore.fetchall()
connessione.close()

print(f'Correzioni registrate: {len(correzioni)}\n')

conteggio_coppie = Counter(
    (originale, corretta) for originale, corretta, _, _ in correzioni
)

for (originale, corretta), volte in conteggio_coppie.most_common():
    print(f'  {originale} -> {corretta}: {volte} volt{"a" if volte == 1 else "e"}')

print('\nDettaglio:')
for originale, corretta, oggetto, data in correzioni:
    print(f'  Oggetto: {oggetto!r}')
    print(f'    originale: {originale}, corretta in: {corretta}  ({data})')