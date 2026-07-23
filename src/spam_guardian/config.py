"""
Caricamento della configurazione da variabili d'ambiente.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # legge il file .env e lo carica in os.environ

CLIENT_ID = os.environ["AZURE_CLIENT_ID"]
AUTHORITY = "https://login.microsoftonline.com/consumers"
SCOPES = ["Mail.ReadWrite"]
CACHE_PATH = "token_cache.bin"
OLLAMA_URL = 'http://localhost:11434/api/generate'
MODELLO_CLASSIFICAZIONE = 'granite4.1:3b'
DB_PATH = 'spam_guardian.db'
NOME_CARTELLA_VERIFICA = 'Da verificare'
SOGLIA_ELIMINAZIONE = 0.90
INTERVALLO_MINUTI = 20