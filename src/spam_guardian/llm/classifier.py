"""
Classifica le email della cartella spam usando un modello LLM locale (Ollama).
"""

import json

import requests

from .. import config

CATEGORIE = [
    'spam_certo',
    'phishing',
    'newsletter',
    'commerciale',
    'probabilmente_importante',
]

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

Attenzione a non confondere "phishing" con "commerciale": se l'email promette premi,
vincite, bonus, giri gratis o denaro non richiesto, spingendo a cliccare con urgenza
per riscuoterlo, è "phishing" anche se il tono sembra pubblicitario — è un classico
schema di truffa, non un'offerta commerciale legittima. Usa "commerciale" solo per
pubblicità reale di prodotti o servizi, senza la logica "hai vinto qualcosa, agisci ora".

Mittente: {mittente}
Oggetto: {oggetto}
Anteprima corpo: {corpo}
'''


def _costruisci_prompt(email: dict) -> str:
    '''Genera il prompt di classificazione a partire dai dati di una email.'''
    mittente = email['from']['emailAddress']['address']
    return PROMPT_TEMPLATE.format(
        categorie=', '.join(CATEGORIE),
        mittente=mittente,
        oggetto=email['subject'],
        corpo=email['bodyPreview'],
    )


def classifica_email(email: dict) -> dict:
    '''
    Classifica una email tramite il modello LLM locale.

    Restituisce un dizionario con le chiavi 'categoria', 'confidenza', 'motivazione'.
    Solleva RuntimeError se Ollama non risponde o restituisce un JSON non valido.
    '''
    prompt = _costruisci_prompt(email)

    corpo_richiesta = {
        'model': config.MODELLO_CLASSIFICAZIONE,
        'prompt': prompt,
        'format': SCHEMA_CLASSIFICAZIONE,
        'stream': False,
    }

    try:
        risposta = requests.post(config.OLLAMA_URL, json=corpo_richiesta, timeout=30)
    except requests.exceptions.ConnectionError as errore:
        raise RuntimeError('Impossibile contattare Ollama. È in esecuzione?') from errore

    if risposta.status_code != 200:
        raise RuntimeError(f'Errore Ollama: {risposta.status_code} - {risposta.text}')

    dati_risposta = risposta.json()

    try:
        return json.loads(dati_risposta['response'])
    except json.JSONDecodeError as errore:
        raise RuntimeError(
            f'JSON non valido dal modello: {dati_risposta["response"]!r}'
        ) from errore