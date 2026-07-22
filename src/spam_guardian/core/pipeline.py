"""
Pipeline: legge le email dalla cartella spam, classifica quelle nuove,
esegue l'azione automatica prevista per la categoria e salva tutto.
"""

from .. import auth, config
from ..db import database, repository
from ..graph import client as graph_client
from ..llm import classifier
from . import azioni


def esegui_pipeline(numero_massimo: int = 20) -> None:
    '''Legge le email dalla cartella spam, classifica quelle nuove, agisce e salva i risultati.'''
    app = auth.crea_app_msal()
    token = auth.ottieni_token(app)

    connessione = database.crea_connessione()
    database.crea_schema(connessione)

    cartella_verifica_id = graph_client.ottieni_o_crea_cartella(token, config.NOME_CARTELLA_VERIFICA)

    email_spam = graph_client.leggi_posta_indesiderata(token, numero_massimo=numero_massimo)
    print(f'Recuperate {len(email_spam)} email.\n')

    for email in email_spam:
        if repository.email_gia_classificata(connessione, email['id']):
            print(f'Oggetto: {email["subject"]} (già classificata, salto)\n')
            continue

        print(f'Oggetto: {email["subject"]}')

        try:
            risultato = classifier.classifica_email(email)
        except RuntimeError as errore:
            print(f'  Errore nella classificazione: {errore}\n')
            continue

        repository.salva_classificazione(connessione, email, risultato)

        try:
            azione = azioni.esegui_azione(token, email, risultato['categoria'], risultato['confidenza'], cartella_verifica_id)
            esito = 'successo'
        except RuntimeError as errore:
            azione = 'nessuna_azione'
            esito = f'errore: {errore}'

        repository.registra_azione(connessione, email['id'], azione, esito)

        print(f'  Categoria: {risultato["categoria"]}')
        print(f'  Confidenza: {risultato["confidenza"]}')
        print(f'  Azione: {azione}\n')

    connessione.close()