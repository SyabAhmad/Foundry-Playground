import requests

try:
    response = requests.get('http://localhost:5000/api/models', timeout=30)
    print(f'Status: {response.status_code}')
    data = response.json()
    print(f'Source: {data.get("source")}')
    print(f'Count: {data.get("count")}')
    models = data.get("models", [])
    print(f'Models: {[m.get("name", m.get("id")) for m in models[:5]]}')
    if models:
        print(f'First model details: {models[0]}')
except Exception as e:
    print(f'Error: {e}')