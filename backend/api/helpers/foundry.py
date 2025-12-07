import requests


def is_foundry_available(foundry_url, timeout=2):
    try:
        url = f"{foundry_url.rstrip('/')}/health"
        resp = requests.get(url, timeout=timeout)
        if resp.status_code == 200:
            return True, resp.json()
        return False, None
    except Exception as e:
        return False, None
