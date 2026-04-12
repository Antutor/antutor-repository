from locust import HttpUser, task, between, TaskSet
import random

"""
Antutor Real-world Benchmark Locust Script
-----------------------------------------
This script tests the actual business logic (News RAG, KG, Multi-Agent Inference)
by comparing the Synchronous Sequential version and the Asynchronous Parallel version.

[CLI Execution Command]
locust -f locustfile.py --headless -u 5 -r 1 --run-time 2m --host http://localhost:8000 --csv real_results
"""

# Realistic student answers for various concepts
STUDENT_ANSWERS = [
    {"concept": "Inflation", "answer": "Inflation is when prices rise and the value of money falls, so we can buy less with the same amount."},
    {"concept": "Opportunity Cost", "answer": "Opportunity cost is the value of the next best alternative that we give up when we make a choice."},
    {"concept": "Interest Rates", "answer": "Interest rates are the cost of borrowing money, usually expressed as a percentage of the total amount."},
    {"concept": "Supply and Demand", "answer": "Supply is how much of something is available, while demand is how much people want to buy it."},
    {"concept": "GDP", "answer": "GDP measures the total value of all goods and services produced in a country over a specific time."}
]

class PerformanceUser(HttpUser):
    wait_time = between(2, 5) # Simulating realistic turn-taking time
    
    @task(1)
    def test_sync_real(self):
        # Pick a random scenario
        scenario = random.choice(STUDENT_ANSWERS)
        payload = {
            "session_id": "benchmark_session",
            "concept": scenario["concept"],
            "user_answer": scenario["answer"]
        }
        self.client.post("/benchmark/sync", json=payload, name="/benchmark/sync")

    @task(1)
    def test_async_real(self):
        scenario = random.choice(STUDENT_ANSWERS)
        payload = {
            "session_id": "benchmark_session",
            "concept": scenario["concept"],
            "user_answer": scenario["answer"]
        }
        self.client.post("/benchmark/async", json=payload, name="/benchmark/async")
