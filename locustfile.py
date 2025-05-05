import random
import time
import hashlib
from datetime import datetime, timezone
from locust import HttpUser, task, constant_throughput


class ApiUser(HttpUser):
    # Each user will send 1 request per second
    wait_time = constant_throughput(1)
    host = "http://127.0.0.1:8000"

    @task
    def create_message(self):
        """Simulates users sending messages to the bot's API endpoint."""
        # Generate unique data for each request
        user_telegram_id = random.randint(1000000, 9999999)
        hashed_user_id = hashlib.sha256(
            str(user_telegram_id).encode()
        ).hexdigest()
        message_text = f"Test message from Locust {time.time()}"
        # Use a realistically large message_id, similar to Telegram
        message_id = random.randint(100000, 999999999)
        current_time_utc = datetime.now(timezone.utc).isoformat()

        payload = {
            "message_id": message_id,
            "user_id": hashed_user_id,
            "message": message_text,
            "created_at": current_time_utc,
        }

        headers = {'Content-Type': 'application/json'}

        self.client.post(
            "/user_messages", json=payload,
            headers=headers, name="/user_messages"
        )
