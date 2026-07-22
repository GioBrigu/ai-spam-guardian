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