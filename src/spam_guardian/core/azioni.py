"""
Azioni automatiche da eseguire in base alla categoria di classificazione.
"""

from ..graph import client as graph_client


def esegui_azione(access_token: str, email: dict, categoria: str, cartella_verifica_id: str) -> str:
    '''
    Esegue l'azione automatica associata alla categoria, se prevista.
    Restituisce una stringa che descrive l'azione (da salvare nel log).
    '''
    if categoria == 'probabilmente_importante':
        graph_client.sposta_email(access_token, email['id'], cartella_verifica_id)
        return 'spostata_in_da_verificare'

    return 'nessuna_azione'