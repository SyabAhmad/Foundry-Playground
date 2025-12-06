import requests

try:
    response = requests.get('http://127.0.0.1:56831/v1/models', timeout=10)
    print(f'Foundry Local Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        models = data.get('data', [])
        print(f'Foundry Local Models: {len(models)}')
        for model in models[:3]:
            print(f'  - {model.get("id")}')
    else:
        print(f'Foundry Local Error: {response.status_code}')
        print(f'Response: {response.text[:200]}')
except Exception as e:
    print(f'Cannot connect to Foundry Local: {e}')