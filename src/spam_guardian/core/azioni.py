"""
Azioni automatiche da eseguire in base alla categoria di classificazione.
"""

from .. import config
from ..graph import client as graph_client


def esegui_azione(access_token: str, email: dict, categoria: str, confidenza: float, cartella_verifica_id: str) -> str:
    '''Esegue l'azione automatica associata alla categoria, se prevista.'''
    if categoria == 'probabilmente_importante':
        graph_client.sposta_email(access_token, email['id'], cartella_verifica_id)
        return 'spostata_in_da_verificare'

    if categoria in ('spam_certo', 'phishing') and confidenza >= config.SOGLIA_ELIMINAZIONE:
        graph_client.elimina_email(access_token, email['id'])
        return 'eliminata'

    return 'nessuna_azione'