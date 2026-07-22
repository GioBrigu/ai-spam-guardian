"""
Pipeline minima: legge le email dalla cartella spam, classifica quelle nuove
e salva il risultato. Le email già classificate in precedenza vengono saltate.
"""

from .. import auth
from ..db import database, repository
from ..graph import client as graph_client
from ..llm import classifier


def esegui_pipeline(numero_massimo: int = 20) -> None:
    '''Legge le email dalla cartella spam, classifica quelle nuove e salva i risultati.'''
    app = auth.crea_app_msal()
    token = auth.ottieni_token(app)

    connessione = database.crea_connessione()
    database.crea_schema(connessione)

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

        print(f'  Categoria: {risultato["categoria"]}')
        print(f'  Confidenza: {risultato["confidenza"]}')
        print(f'  Motivazione: {risultato["motivazione"]}\n')

    connessione.close()