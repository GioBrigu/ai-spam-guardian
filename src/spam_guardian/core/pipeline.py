"""
Pipeline minima: legge le email dalla cartella spam e le classifica.
Versione senza salvataggio su database — arriverà in una milestone successiva.
"""

from .. import auth
from ..graph import client as graph_client
from ..llm import classifier


def esegui_pipeline(numero_massimo: int = 20) -> None:
    '''Legge le email dalla cartella spam, le classifica e stampa il risultato di ciascuna.'''
    app = auth.crea_app_msal()
    token = auth.ottieni_token(app)

    email_spam = graph_client.leggi_posta_indesiderata(token, numero_massimo=numero_massimo)
    print(f'Recuperate {len(email_spam)} email.\n')

    for email in email_spam:
        print(f'Oggetto: {email["subject"]}')

        try:
            risultato = classifier.classifica_email(email)
        except RuntimeError as errore:
            print(f'  Errore nella classificazione: {errore}\n')
            continue

        print(f'  Categoria: {risultato["categoria"]}')
        print(f'  Confidenza: {risultato["confidenza"]}')
        print(f'  Motivazione: {risultato["motivazione"]}\n')