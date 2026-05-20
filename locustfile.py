from locust import HttpUser, task, between

class AntutorUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def test_chat_api(self):
        # 실제 데이터베이스에 등록되어 있는 유효한 세션(147)과 concept 필드를 포함하여 요청합니다.
        # 인증 오류(401, 403) 및 검증 오류(422)를 방지하기 위해 유효한 토큰을 사용합니다.
        self.client.post("/chat", json={
            "session_id": "147",
            "concept": "inflation",
            "user_answer": "물건 가격이 전반적으로 꾸준히 상승하는 것을 의미해."
        }, headers={
            "Authorization": "Bearer YOUR_JWT_TOKEN"
        })
