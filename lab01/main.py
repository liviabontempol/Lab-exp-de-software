import os
from dotenv import load_dotenv

load_dotenv() # Carrega as variáveis do arquivo .env

token = os.getenv("API_TOKEN")

headers = {
    "Authorization": f"Bearer {token}"
}
response = requests.get("https://api.github.com/user", headers=headers)
if response.status_code == 200:
    user_data = response.json()
    print(f"Olá, {user_data['login']}!")   
else:
    print("Falha ao autenticar. Verifique seu token.")  
