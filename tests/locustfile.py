"""Load test: locust -f tests/locustfile.py --host=http://localhost:8000"""
from locust import HttpUser, between, task


class RecUser(HttpUser):
    wait_time = between(0.5, 2)
    token: str = ""

    def on_start(self):
        r = self.client.post("/auth/login",
                             json={"email": "user0@example.com", "password": "password123"})
        if r.status_code == 200:
            self.token = r.json()["access_token"]

    def _h(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(5)
    def home(self):
        self.client.get("/recommendations/home?limit=20", headers=self._h())

    @task(2)
    def trending(self):
        self.client.get("/recommendations/trending?limit=20", headers=self._h())

    @task(2)
    def search_suggest(self):
        self.client.get("/search/suggest?q=dark", headers=self._h())

    @task(1)
    def taste_dna(self):
        self.client.get("/users/me/taste-dna", headers=self._h())

    @task(1)
    def batch(self):
        self.client.post("/recommendations/batch",
                         json={"surfaces": ["home", "trending", "new_releases"], "limit": 10},
                         headers=self._h())
