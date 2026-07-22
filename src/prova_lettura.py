from spam_guardian import auth
from spam_guardian.graph import client

app = auth.crea_app_msal()
token = auth.ottieni_token(app)

email = client.leggi_posta_indesiderata(token, numero_massimo=10)

for e in email:
    mittente = e["from"]["emailAddress"]["address"] if e.get("from") else "sconosciuto"
    print(f"- {e['receivedDateTime']} | {mittente} | {e['subject']}")