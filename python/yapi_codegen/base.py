import requests


class ApiBase:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()

    def request(self, method: str, url: str, **kwargs) -> dict:
        if not url.startswith("http"):
            url = f"{self.base_url}/{url.lstrip("/")}"
        response = self._session.request(method, url, **kwargs)
        if not response.ok:
            print(f'Response Error: [{response.status_code}] {response.text}')
        response_body = response.json()
        return response_body['data']

    def get(self, url) -> dict:
        return self.request('GET', url)

    def post(self, url, payload) -> dict:
        return self.request('POST', url, json=payload)
