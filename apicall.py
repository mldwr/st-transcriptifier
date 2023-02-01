import requests

url = "http://localhost:8000/letter_count"

msg = "hello world dudes"
payload = {"text": msg}

response = requests.post(url, json=payload)

print(payload, response.json())

