# AI Spam Guardian

App desktop che classifica automaticamente le email della cartella "Posta indesiderata" di Outlook usando un modello LLM locale, per ridurre il tempo speso a controllarla manualmente.

## Il problema

L'account Outlook che uso riceve centinaia di email di spam al giorno. Outlook sposta quasi tutto in automatico in "Posta indesiderata", ma qualche email legittima ci finisce comunque (raramente) — quindi va comunque controllata manualmente, centinaia di email al giorno per trovarne una importante ogni tanto.

## Obiettivo

Non il miglior filtro antispam del mondo, ma ridurre quasi a zero il tempo speso a controllare quella cartella. Con un LLM locale: nessuna API a pagamento, nessun dato che esce dal computer.

## Come funziona (in sviluppo)

1. Autenticazione a Outlook via Microsoft Graph (OAuth2 con MSAL)
2. Lettura periodica della cartella "Posta indesiderata"
3. Classificazione di ogni email con un LLM locale (Ollama) in 5 categorie: spam certo, phishing, newsletter, commerciale, probabilmente importante
4. Azione automatica in base alla categoria (con salvaguardie)
5. Apprendimento nel tempo dal feedback dell'utente

## Stack tecnologico

- Python
- Microsoft Graph API (lettura/gestione email)
- Ollama + granite4.1:3b (classificazione LLM locale)
- SQLite (storico classificazioni e feedback)
- PySide6 (interfaccia desktop)

## Decisioni tecniche

- **Scelta del modello LLM**: confrontati 3 modelli locali (qwen3.5:4b, phi4-mini, granite4.1:3b) su 19 email reali di spam, verificate a mano una per una come verità di riferimento. `granite4.1:3b` ha classificato correttamente come phishing 7/19 email contro le 2/19 di `phi4-mini`; `qwen3.5:4b` escluso perché non rispettava mai il formato JSON richiesto.
- **Architettura**: pattern Repository/Strategy/Adapter per isolare la logica di business dai servizi esterni (Graph API, Ollama, database).
- **Sicurezza**: token di autenticazione cifrato con DPAPI (Windows), credenziali mai salvate in chiaro e escluse da Git.

## Stato del progetto

- [x] Analisi requisiti e architettura
- [x] Autenticazione Microsoft Graph
- [x] Lettura email dalla cartella spam
- [x] Scelta e validazione del modello LLM
- [ ] Classificazione email nella pipeline reale
- [ ] Salvataggio su database e logica delle azioni
- [ ] Interfaccia desktop
- [ ] Apprendimento dal feedback utente

## Setup locale

Prerequisiti: Python, [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com) con il modello scaricato (`ollama pull granite4.1:3b`), un'app registrata su Azure AD per ottenere un `AZURE_CLIENT_ID`.

```bash
git clone <url-del-repository>
cd ai-spam-guardian
uv sync
echo "AZURE_CLIENT_ID=il-tuo-client-id" > .env
```

## Autore

Progetto realizzato da Giovanni durante il percorso ITS Big Data Specialist, come esercizio pratico di transizione verso ruoli data (Data Analyst / BI Analyst), a partire da un background di 15+ anni in customer care e project management.