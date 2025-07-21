
import asyncio
import httpx
import random

import string
import time
import json
import argparse
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")


def random_task():
    return {
        "title": "Task " + "".join(random.choices(string.ascii_letters, k=5)),
        "description": "Description " + "".join(random.choices(string.ascii_letters, k=10)),
        "deadline": (datetime.now(timezone.utc) + timedelta(days=random.randint(1, 10))).isoformat(),
        "status": random.choice(["pending", "in_progress", "completed"])
    }


async def call(client, method, url, label=None, **kwargs):
    full_url = BASE_URL + url
    label = label or f"{method.upper()} {url}"
    print(f"\n{label}")
    start = time.time()

    try:
        response = await getattr(client, method.lower())(full_url, **kwargs)
    except Exception as e:
        print(f"Request failed: {e}")
        return {}, 0.0

    duration = round(time.time() - start, 4)
    print(f"Time: {duration}s | Status: {response.status_code}")

    try:
        data = response.json() if isinstance(response, httpx.Response) else {}
        if asyncio.iscoroutine(data):
            data = await data
        print("Response:", data.get("message") or data.get("detail") or "...")
    except Exception as e:
        print("Failed to parse JSON:", e)
        print("Raw response:", response.text)
        data = {}

    return data, duration


async def test_api(fake_count: int):
    async with httpx.AsyncClient() as client:
        await call(client, "GET", "/")

        max_retries = 2
        for attempt in range(1, max_retries + 1):
            print(f"\nAttempt {attempt} to create {fake_count} fake tasks")
            create_resp, _ = await call(client, "POST", f"/tasks/fake/{fake_count}")
            created_count = create_resp.get("count", 0)

            percent = (created_count / fake_count) * 100 if fake_count else 0
            print(f"Created {created_count}/{fake_count} tasks ({percent:.2f}%)")

            if created_count == fake_count:
                break
            elif attempt < max_retries:
                print("Retrying...")
                await asyncio.sleep(1)
            else:
                print("Max attempts reached. Moving on...")

        await asyncio.sleep(2)

        all_tasks_resp, t1 = await call(client, "GET", "/alltasks", label="GET /tasks (1st - Cold)")
        actual_count = all_tasks_resp.get("count", 0)
        count_percent = (actual_count / fake_count) * 100 if fake_count else 0
        print(f"\nDB Count: {actual_count}/{fake_count} ({count_percent:.2f}%)")

        _, t2 = await call(client, "GET", "/alltasks", label="GET /tasks (2nd - Cached?)")
        if t1 > 0:
            improvement = ((t1 - t2) / t1) * 100
            print(f"\nCache test: Cold = {t1}s, Cached = {t2}s, Improvement = {improvement:.2f}%")
        else:
            print(f"\nCache test: Cold = {t1}s, Cached = {t2}s")

        tasks = all_tasks_resp.get("tasks", [])
        if not tasks:
            print("No tasks found. Exiting.")
            return

        new_task_data, _ = await call(client, "POST", "/addtasks", json=random_task())
        new_task_id = new_task_data.get("task", {}).get("id", "")
        existing_id = tasks[0].get("id", "")

        if existing_id:
            await call(client, "PUT", f"/updatetasks/{existing_id}", json={"title": "Updated Title"})
            await call(client, "DELETE", f"/deletetask/{existing_id}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Task API routes")
    parser.add_argument("--fake", type=int, default=10, help="Number of fake tasks to generate")
    args = parser.parse_args()

    print(f"Starting Task API Route Test with {args.fake} fake tasks")
    start = time.time()
    asyncio.run(test_api(args.fake))
    print(f"\nCompleted in {round(time.time() - start, 2)} seconds")

