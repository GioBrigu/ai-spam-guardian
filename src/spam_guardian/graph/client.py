"""
Client per leggere le email dalla cartella "Posta indesiderata" via Microsoft Graph.
"""

import requests

GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"


def leggi_posta_indesiderata(access_token: str, numero_massimo: int = 25) -> list[dict]:
    """
    Recupera le email più recenti dalla cartella "Posta indesiderata".

    Usa il nome di cartella predefinito "junkemail" (well-known folder name),
    che Microsoft Graph riconosce senza bisogno di conoscerne l'ID interno.
    """
    url = f"{GRAPH_BASE_URL}/me/mailFolders/junkemail/messages"

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    parametri = {
        "$select": "id,subject,from,receivedDateTime,bodyPreview",
        "$top": numero_massimo,
        "$orderby": "receivedDateTime desc",
    }

    risposta = requests.get(url, headers=headers, params=parametri)

    if risposta.status_code != 200:
        raise RuntimeError(
            f"Errore Graph API: {risposta.status_code} - {risposta.text}"
        )

    dati = risposta.json()
    return dati["value"]  # Graph incapsula sempre i risultati dentro "value"


def ottieni_o_crea_cartella(access_token: str, nome_cartella: str) -> str:
    '''Restituisce l'id della cartella con questo nome; la crea se non esiste ancora.'''
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f'{GRAPH_BASE_URL}/me/mailFolders'

    risposta = requests.get(url, headers=headers, params={'$filter': f"displayName eq '{nome_cartella}'"})
    if risposta.status_code != 200:
        raise RuntimeError(f'Errore Graph API: {risposta.status_code} - {risposta.text}')

    cartelle_trovate = risposta.json()['value']
    if cartelle_trovate:
        return cartelle_trovate[0]['id']

    risposta_creazione = requests.post(url, headers=headers, json={'displayName': nome_cartella})
    if risposta_creazione.status_code != 201:
        raise RuntimeError(
            f'Errore creazione cartella: {risposta_creazione.status_code} - {risposta_creazione.text}'
        )

    return risposta_creazione.json()['id']


def sposta_email(access_token: str, email_id: str, cartella_destinazione_id: str) -> None:
    '''Sposta un'email nella cartella indicata.'''
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f'{GRAPH_BASE_URL}/me/messages/{email_id}/move'

    risposta = requests.post(url, headers=headers, json={'destinationId': cartella_destinazione_id})
    if risposta.status_code != 201:
        raise RuntimeError(f'Errore spostamento email: {risposta.status_code} - {risposta.text}')


def elimina_email(access_token: str, email_id: str) -> None:
    '''Elimina un'email (viene spostata in "Posta eliminata", recuperabile per un periodo)'''
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f'{GRAPH_BASE_URL}/me/messages/{email_id}'

    risposta = requests.delete(url, headers=headers)
    if risposta.status_code != 204:
        raise RuntimeError(f'Errore eliminazione email: {risposta.status_code} - {risposta.text}')