import requests

try:
    response = requests.get('http://localhost:5000/api/models', timeout=10)
    print(f'Status: {response.status_code}')
    data = response.json()
    print(f'Source: {data.get("source")}')
    print(f'Count: {data.get("count")}')
    print(f'Models: {data.get("models", [])}')
except Exception as e:
    print(f'Error: {e}')