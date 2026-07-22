# AI Spam Guardian — Documento di Design

**Milestone 0 — Analisi dei requisiti e Architettura**

> Destinazione consigliata nel repository: `docs/architettura.md`

---

## 1. Obiettivo del progetto

Il problema non è bloccare lo spam (Outlook lo fa già bene), ma il tempo speso a
controllare manualmente centinaia di email nella cartella "Posta indesiderata"
per non perdere, molto raramente, un'email importante.

**Obiettivo:** un'app desktop Windows che monitora la cartella spam via
Microsoft Graph, classifica le email con un LLM locale (Ollama), recupera
automaticamente quelle probabilmente legittime e propone all'utente di
eliminare definitivamente lo spam ad altissima confidenza — con salvaguardie.

Non è l'obiettivo costruire il miglior antispam del mondo: è eliminare quasi
del tutto il tempo di controllo manuale.

---

## 2. Requisiti funzionali

| # | Requisito |
|---|---|
| 1 | Autenticarsi al proprio account Outlook via Microsoft Graph |
| 2 | Leggere periodicamente le nuove email nella cartella "Posta indesiderata" |
| 3 | Classificare ogni email: spam certo / phishing / newsletter / commerciale / probabilmente importante |
| 4 | Spostare le email "probabilmente importanti" in una cartella "Da verificare" |
| 5 | Eliminare definitivamente lo spam ad altissima confidenza, solo con salvaguardie |
| 6 | Registrare le correzioni manuali dell'utente per migliorare la classificazione nel tempo |
| 7 | Mostrare statistiche/dashboard sull'attività |

## 3. Requisiti non funzionali

- Nessuna API AI a pagamento → LLM locale via Ollama
- Deve girare su hardware modesto: CPU (AMD Ryzen 7 5700U), 16 GB RAM, **nessuna GPU dedicata** → modello LLM leggero, quantizzato
- App desktop Windows
- Dati (contenuto email, decisioni, feedback) restano sempre in locale — nessun dato lascia il PC
- **Estendibile** (facile sostituire un componente, es. altro motore LLM) — non richiede scalabilità (uso singolo utente)

---

## 4. Attori

| Attore | Ruolo |
|---|---|
| 👤 Utente | Autentica l'app, revisiona/corregge classificazioni, configura soglie, consulta statistiche |
| ⏱️ Scheduler | Attore automatico: innesca la scansione periodica senza intervento umano |
| 🌐 Microsoft Graph API | Sistema esterno: fornisce accesso alla cassetta Outlook |
| 🧠 LLM locale (Ollama) | Sistema esterno: esegue la classificazione delle email |

## 5. Casi d'uso

1. Autenticarsi con Microsoft Graph
2. Scansionare la cartella "Posta indesiderata" *(avviato dallo Scheduler)*
3. Classificare un'email *(caso d'uso centrale, richiamato da quasi tutti gli altri)*
4. Spostare un'email in "Da verificare"
5. Eliminare definitivamente un'email (solo altissima confidenza + salvaguardie)
6. Revisionare/correggere una classificazione
7. Registrare il feedback per migliorare la classificazione futura
8. Visualizzare statistiche/dashboard
9. Configurare soglie di confidenza e impostazioni

**Relazioni `<<include>>`** (un caso d'uso che ne richiama sempre un altro):

```
Scansionare cartella
   └─ <<include>> ──▶ Classificare un'email
                          ├─ <<include>> ──▶ Spostare in "Da verificare"
                          ├─ <<include>> ──▶ Eliminare definitivamente
                          └─ <<include>> ──▶ Registrare feedback (se l'utente corregge)
```

---

## 6. Flusso dei dati

```
1. Scheduler → sveglia il programma ogni N minuti
2. Programma → chiama Microsoft Graph API: "dammi le nuove email in Posta indesiderata"
3. Per ogni nuova email:
     a. Estrai mittente, oggetto, corpo, eventuali link
     b. Invia i dati al modello LLM locale (Ollama) → richiesta di classificazione
     c. LLM restituisce: categoria + livello di confidenza
     d. Salva il risultato in SQLite (email + categoria + confidenza + timestamp)
     e. In base a categoria/confidenza:
          - alta confidenza "importante"      → sposta in "Da verificare"
          - altissima confidenza "spam"       → elimina (con log)
          - tutto il resto                    → resta in Posta indesiderata, solo loggato
4. Dashboard → legge da SQLite e mostra statistiche
5. Se l'utente corregge una classificazione → il correttivo viene salvato come feedback (Milestone 5)
```

Il punto 3b (chiamata all'LLM) è il più delicato: è lento e può fallire — va gestito con
attenzione (async/threading, per non bloccare la GUI).

---

## 7. Struttura del progetto

Uso lo **"src layout"** (standard moderno in Python): il pacchetto vive dentro `src/`,
così non è raggiungibile "per sbagliato" dalla cartella corrente e va sempre installato
correttamente — evita il bug "funziona sul mio PC ma non altrove".

```
ai-spam-guardian/
├── pyproject.toml           ← config progetto + dipendenze (gestito da uv)
├── README.md
├── .env.example              ← esempio variabili di configurazione (mai il vero .env su Git!)
├── .gitignore
├── docs/
│   └── architettura.md       ← questo documento
├── src/
│   └── spam_guardian/
│       ├── main.py            ← entry point dell'app
│       ├── config.py          ← caricamento configurazione
│       ├── graph/              ← tutto ciò che parla con Microsoft Graph
│       │   ├── auth.py         ← OAuth (MSAL)
│       │   └── client.py       ← leggi/sposta/elimina email
│       ├── llm/                ← tutto ciò che parla con Ollama
│       │   └── classifier.py
│       ├── db/                 ← tutto ciò che parla con SQLite
│       │   ├── models.py       ← schema tabelle
│       │   └── repository.py   ← query CRUD
│       ├── core/
│       │   └── pipeline.py     ← orchestra: scansiona → classifica → agisci
│       ├── scheduler.py        ← timer periodico
│       ├── gui/
│       │   ├── main_window.py
│       │   └── dashboard.py
│       └── logging_config.py
└── tests/                     ← rispecchia la struttura di src/
    ├── test_graph.py
    ├── test_llm.py
    ├── test_db.py
    └── test_pipeline.py
```

Ogni cartella = una responsabilità (Single Responsibility). Cambiare motore LLM tocca
solo `llm/`; cambiare DB tocca solo `db/`.

---

## 8. Design pattern adottati

Filo conduttore: `pipeline.py` (il cuore del sistema) parla solo con **interfacce
astratte**, mai con i dettagli concreti — "programmare verso un'interfaccia, non verso
un'implementazione".

### Repository pattern → per il database

Nasconde i dettagli SQL dietro metodi semplici, così il resto del programma non sa
nemmeno che sotto c'è SQLite.

```python
class EmailRepository:
    def salva_email(self, email: Email) -> None:
        ...  # qui dentro c'è SQL/SQLite

    def trova_da_verificare(self) -> list[Email]:
        ...
```

### Strategy pattern → per la logica di decisione

Incapsula la regola "se confidenza > X → elimina" in un oggetto intercambiabile,
invece di `if/elif` sparsi nel codice.

```python
class StrategiaConfidenza:
    def decidi(self, categoria: str, confidenza: float) -> str:
        ...  # ritorna 'elimina' / 'da_verificare' / 'ignora'
```

### Adapter pattern → per l'LLM

Un'interfaccia comune, così `OllamaClassifier` è solo *una* implementazione possibile.

```python
class ClassificatoreLLM:
    def classifica(self, email: Email) -> Classificazione:
        raise NotImplementedError

class OllamaClassifier(ClassificatoreLLM):
    def classifica(self, email: Email) -> Classificazione:
        ...  # qui la chiamata a Ollama
```

---

## 9. Schema del database (SQLite)

### `emails` — una riga per ogni email analizzata

| Campo | Tipo | Note |
|---|---|---|
| `id` | INTEGER PK | |
| `graph_message_id` | TEXT, **unico** | ID Microsoft Graph — evita di riprocessare la stessa email (idempotenza) |
| `mittente` | TEXT | |
| `oggetto` | TEXT | |
| `ricevuta_il` | DATETIME | |
| `categoria` | TEXT | spam_certo / phishing / newsletter / commerciale / probabile_importante |
| `confidenza` | REAL (0.0–1.0) | |
| `azione` | TEXT | eliminata / spostata / ignorata |
| `processata_il` | DATETIME | |

### `feedback` — correzioni manuali (per Milestone 5)

| Campo | Tipo | Note |
|---|---|---|
| `id` | INTEGER PK | |
| `email_id` | INTEGER, FK → `emails.id` | |
| `categoria_originale` | TEXT | |
| `categoria_corretta` | TEXT | |
| `corretta_il` | DATETIME | |

### `azioni_log` — audit trail delle azioni distruttive

| Campo | Tipo | Note |
|---|---|---|
| `id` | INTEGER PK | |
| `email_id` | INTEGER, FK → `emails.id` | |
| `tipo_azione` | TEXT | eliminata / spostata / ripristinata |
| `timestamp` | DATETIME | |
| `esito` | TEXT | successo / errore |

Separata dai log tecnici: è la "scatola nera" delle decisioni distruttive — se
un'email importante sparisce, qui c'è la prova di cosa è successo.

### `impostazioni` — soglie configurabili da GUI

| Campo | Tipo |
|---|---|
| `chiave` | TEXT PK (es. `soglia_eliminazione`) |
| `valore` | TEXT |

---

## 10. Strategia di logging (tecnico, diverso da `azioni_log`)

Modulo `logging` di Python, su file con **rotazione** (max 5 file da 5 MB):

| Livello | Uso |
|---|---|
| `DEBUG` | dettagli tecnici (solo sviluppo) |
| `INFO` | eventi normali ("scansione avviata", "5 email trovate") |
| `WARNING` | anomalie non bloccanti ("LLM lento, 8s") |
| `ERROR` | operazione fallita ("connessione a Graph fallita") |

## 11. Gestione degli errori

Regola guida per un sistema che agisce in autonomia in modo irreversibile:

> **In caso di dubbio o errore, il default è NON agire.** Se la classificazione
> fallisce o il risultato non è chiaro, l'email resta dov'è.

`try/except` mirati per ogni chiamata esterna, con **retry** (2-3 tentativi, attesa
crescente) solo per errori transitori di rete — non per errori di autenticazione,
che richiedono intervento umano.

## 12. Configurazione

Nessun valore variabile scritto fisso nel codice (soglie, cartelle, nome modello,
intervallo scheduler). Tutto in un file `.env`, separato dal codice.

## 13. Sicurezza e privacy

- Autenticazione via **MSAL** (libreria ufficiale Microsoft), permessi minimi
  necessari (*least privilege*: solo lettura/scrittura sulla cartella spam)
- Token mai in chiaro: MSAL li cifra in una cache locale
- `.env` e cache token sempre in `.gitignore`, mai su Git
- Contenuto delle email mai fuori dal PC: LLM locale → vantaggio di privacy
  rispetto a soluzioni cloud a pagamento

---

## 14. Prossimi passi

- **Milestone 1** — Autenticazione Microsoft Graph (OAuth, token, permessi)
- **Milestone 2** — Lettura email dalla cartella spam
- **Milestone 3** — Scelta e integrazione del modello LLM locale
- **Milestone 4** — Logica di recupero/eliminazione con salvaguardie
- **Milestone 5** — Apprendimento dal feedback + statistiche/dashboard
- **Milestone 6** — GUI desktop
