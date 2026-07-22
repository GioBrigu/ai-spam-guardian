from spam_guardian import auth

app = auth.crea_app_msal()
token = auth.ottieni_token(app)
print("Token ottenuto, primi 20 caratteri:", token[:20])