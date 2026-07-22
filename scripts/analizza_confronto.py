"""
Analizza confronto_modelli.csv e produce un riepilogo per modello:
- affidabilita nel rispettare il formato JSON richiesto
- tempo medio di risposta
- confidenza media dichiarata
- distribuzione delle categorie assegnate
- percentuale di email su cui i tre modelli sono d'accordo

Uso (dalla cartella dove si trova il CSV):
    uv run scripts/analizza_confronto.py
"""

import json

import pandas as pd

df = pd.read_csv('confronto_modelli.csv')

def estrai_campi(risposta_json: str) -> pd.Series:
    '''Interpreta la risposta del modello come JSON; se fallisce, segna l'errore invece di bloccarsi.'''
    try:
        dati = json.loads(risposta_json)
        return pd.Series({
            'categoria': dati.get('categoria'),
            'confidenza': dati.get('confidenza'),
            'json_valido': True,
        })
    except (json.JSONDecodeError, TypeError):
        return pd.Series({'categoria': None, 'confidenza': None, 'json_valido': False})


# apply() esegue estrai_campi su ogni riga della colonna 'risposta_json';
# siccome la funzione restituisce piu' valori (una pd.Series), il risultato
# si puo' assegnare direttamente a piu' colonne nuove insieme
df[['categoria', 'confidenza', 'json_valido']] = df['risposta_json'].apply(estrai_campi)

print('=== Affidabilita formato JSON (per modello) ===')
print(df.groupby('modello')['json_valido'].mean().round(2), '\n')

print('=== Tempo medio di risposta in secondi (per modello) ===')
print(df.groupby('modello')['durata_secondi'].mean().round(2), '\n')

print('=== Confidenza media dichiarata (per modello) ===')
print(df.groupby('modello')['confidenza'].mean().round(2), '\n')

print('=== Categorie assegnate (per modello) ===')
# groupby su due colonne + size() conta quante righe cadono in ogni combinazione;
# unstack() trasforma il risultato in una tabella modello x categoria
print(df.groupby(['modello', 'categoria']).size().unstack(fill_value=0), '\n')

# pivot riorganizza i dati: una riga per email, una colonna per modello,
# cella = categoria assegnata da quel modello a quella email
confronto_per_email = df.pivot(index='email_id', columns='modello', values='categoria')

# nunique(axis=1) conta, per ogni riga, quanti valori DIVERSI compaiono tra i modelli:
# se vale 1, vuol dire che tutti e tre hanno dato la stessa categoria
confronto_per_email['tutti_daccordo'] = confronto_per_email.nunique(axis=1) == 1

percentuale_accordo = confronto_per_email['tutti_daccordo'].mean().round(2)
print(f"=== Percentuale email con accordo unanime tra i tre modelli: {percentuale_accordo} ===")

confronto_per_email.to_csv('confronto_per_email.csv')
print("Dettaglio email per email salvato in 'confronto_per_email.csv'")

# Casi in cui i due modelli non sono d'accordo su "probabilmente_importante"
casi_da_leggere = confronto_per_email[
    (confronto_per_email['phi4-mini'] == 'probabilmente_importante') |
    (confronto_per_email['granite4.1:3b'] == 'probabilmente_importante')
]

info_email = df[['email_id', 'oggetto']].drop_duplicates()
casi_leggibili = casi_da_leggere.reset_index().merge(info_email, on='email_id')

for _, riga in casi_leggibili.iterrows():
    print(f"Oggetto: {riga['oggetto']}")
    print(f"  granite4.1:3b -> {riga['granite4.1:3b']}")
    print(f"  phi4-mini     -> {riga['phi4-mini']}")
    print()