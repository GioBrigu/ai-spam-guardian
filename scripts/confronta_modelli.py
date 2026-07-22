"""
Confronta due modelli Ollama sulla classificazione delle email
recuperate dalla cartella "Posta indesiderata".

Uso (dalla root del progetto):
    uv run scripts/confronta_modelli.py

Prerequisiti:
    - Ollama in esecuzione in locale (porta di default 11434)
    - Modelli già scaricati con `ollama pull <nome>`
"""

import csv
import time

import requests

from spam_guardian import auth
from spam_guardian.graph import client as graph_client

# Nomi esatti dei modelli così come compaiono in `ollama list`
# qwen3.5:4b escluso dal primo confronto: 0% di risposte in JSON valido
MODELLI = ['phi4-mini', 'granite4.1:3b']

OLLAMA_URL = 'http://localhost:11434/api/generate'

# Categorie decise in Milestone 0
CATEGORIE = [
    'spam_certo',
    'phishing',
    'newsletter',
    'commerciale',
    'probabilmente_importante',
]

# Schema JSON che Ollama userà per vincolare l'output: 'enum' costringe il
# modello a scegliere ESATTAMENTE una delle stringhe elencate per 'categoria',
# niente varianti inventate come nel primo confronto
SCHEMA_CLASSIFICAZIONE = {
    'type': 'object',
    'properties': {
        'categoria': {
            'type': 'string',
            'enum': CATEGORIE,
        },
        'confidenza': {
            'type': 'number',
        },
        'motivazione': {
            'type': 'string',
        },
    },
    'required': ['categoria', 'confidenza', 'motivazione'],
}

PROMPT_TEMPLATE = '''Sei un assistente che classifica email italiane finite nella cartella spam.
Analizza l'email seguente e rispondi SOLO con un oggetto JSON con questi campi:
- "categoria": una tra {categorie}
- "confidenza": numero da 0 a 1
- "motivazione": massimo una frase, in italiano

Mittente: {mittente}
Oggetto: {oggetto}
Anteprima corpo: {corpo}
'''


def costruisci_prompt(email: dict) -> str:
    '''Genera il prompt di classificazione a partire dai dati di una email.'''
    mittente = email['from']['emailAddress']['address']
    return PROMPT_TEMPLATE.format(
        categorie=', '.join(CATEGORIE),
        mittente=mittente,
        oggetto=email['subject'],
        corpo=email['bodyPreview'],
    )


def classifica_con_modello(prompt: str, modello: str) -> dict:
    '''Invia il prompt a un modello Ollama e restituisce risposta grezza + tempo impiegato.'''
    corpo_richiesta = {
        'model': modello,
        'prompt': prompt,
        'format': SCHEMA_CLASSIFICAZIONE,  # vincola sia la struttura sia i valori ammessi
        'stream': False,    # vogliamo la risposta intera in un colpo solo, non a pezzi
    }

    inizio = time.time()
    risposta = requests.post(OLLAMA_URL, json=corpo_richiesta)
    durata = time.time() - inizio

    if risposta.status_code != 200:
        raise RuntimeError(
            f'Errore Ollama ({modello}): {risposta.status_code} - {risposta.text}'
        )

    dati = risposta.json()
    return {
        'risposta_grezza': dati['response'],
        'durata_secondi': round(durata, 2),
    }


def main():
    # 1. Autenticazione e lettura email (riusiamo i moduli già scritti)
    app = auth.crea_app_msal()
    token = auth.ottieni_token(app)
    email_spam = graph_client.leggi_posta_indesiderata(token, numero_massimo=20)

    print(f'Recuperate {len(email_spam)} email da classificare.')

    risultati = []

    # 2. Per ogni email, interroga entrambi i modelli con lo stesso prompt
    for email in email_spam:
        prompt = costruisci_prompt(email)

        for modello in MODELLI:
            print(f'-> {email["subject"][:40]!r} con {modello}...')
            esito = classifica_con_modello(prompt, modello)

            risultati.append({
                'email_id': email['id'],
                'oggetto': email['subject'],
                'modello': modello,
                'risposta_json': esito['risposta_grezza'],
                'durata_secondi': esito['durata_secondi'],
            })

    # 3. Salva tutto in CSV per la valutazione manuale
    with open('confronto_modelli.csv', 'w', newline='', encoding='utf-8') as file_csv:
        scrittore = csv.DictWriter(file_csv, fieldnames=risultati[0].keys())
        scrittore.writeheader()
        scrittore.writerows(risultati)

    print('Fatto. Risultati salvati in confronto_modelli.csv')


if __name__ == '__main__':
    main()