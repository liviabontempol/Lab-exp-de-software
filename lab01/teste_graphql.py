import os
import requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("API_TOKEN")

url = "https://api.github.com/graphql"
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "LabExpSoftware/1.0 (Windows)"
}

query = "query { viewer { login } }"

r = requests.post(url, json={"query": query}, headers=headers, timeout=30)
print("Status:", r.status_code)
print(r.text[:800])