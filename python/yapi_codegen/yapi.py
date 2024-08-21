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

class YApi(ApiBase):
    def login(self, email: str, password: str) -> dict:
        url = "/api/user/login"
        payload = {"email": email, "password": password}
        return self.post(url, payload)

    def get_interface_list(self, project_id, page=1, limit=10) -> list[dict]:
        url = f"/api/interface/list?page={page}&limit={limit}&project_id={project_id}"
        return self.get(url)["list"]
    
    def get_interface_detail(self, interface_id) -> dict:
        url = f"/api/interface/get?id={interface_id}"
        return self.get(url)
