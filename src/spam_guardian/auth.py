"""
Autenticazione a Microsoft Graph via MSAL.
"""

import msal
from msal_extensions import PersistedTokenCache, FilePersistenceWithDataProtection

from . import config


def _crea_cache_sicura() -> PersistedTokenCache:
    """
    Cache dei token cifrata con DPAPI (Windows Data Protection API):
    i dati vengono cifrati con una chiave legata al tuo account utente
    Windows. Nessun altro utente/processo sullo stesso PC, e nessuno
    che copi il file su un altro computer, può decifrarlo.
    """
    persistenza = FilePersistenceWithDataProtection(config.CACHE_PATH)
    return PersistedTokenCache(persistenza)


def crea_app_msal() -> msal.PublicClientApplication:
    """Istanza dell'app MSAL, collegata alla cache sicura."""
    cache = _crea_cache_sicura()
    return msal.PublicClientApplication(
        client_id=config.CLIENT_ID,
        authority=config.AUTHORITY,
        token_cache=cache,
    )


def ottieni_token(app: msal.PublicClientApplication) -> str:
    """
    Restituisce un access token valido.

    1. Prova il login silenzioso: se in cache c'è già un account con
       refresh token valido, MSAL lo usa senza aprire il browser.
    2. Solo se fallisce (prima esecuzione, o token scaduto/revocato),
       apre il browser per il login interattivo (Authorization Code + PKCE,
       gestito internamente da MSAL — non dobbiamo scrivere quella parte).
    """
    accounts = app.get_accounts()
    account = accounts[0] if accounts else None

    risultato = None
    if account:
        risultato = app.acquire_token_silent(config.SCOPES, account=account)

    if not risultato:
        risultato = app.acquire_token_interactive(scopes=config.SCOPES)

    if "access_token" not in risultato:
        errore = risultato.get("error_description", "errore sconosciuto")
        raise RuntimeError(f"Autenticazione fallita: {errore}")

    return risultato["access_token"]