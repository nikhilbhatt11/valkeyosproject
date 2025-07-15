
import asyncio
import httpx
import random
import string
import time
import json
import argparse
import os
import shutil
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv 

load_dotenv()



BASE_URL = os.getenv("BASE_URL")
LOG_DIR = os.getenv("LOG_DIR")
SAVE_RESPONSES = os.getenv("SAVE_RESPONSES")



def prepare_logs():
    if os.path.exists(LOG_DIR):
        shutil.rmtree(LOG_DIR)
    os.makedirs(LOG_DIR)

def random_task():
    return {
        "title": "Task " + "".join(random.choices(string.ascii_letters, k=5)),
        "description": "Description " + "".join(random.choices(string.ascii_letters, k=10)),
        "deadline": (datetime.now(timezone.utc) + timedelta(days=random.randint(1, 10))).isoformat(),
        "status": random.choice(["pending", "in_progress", "completed"])
    }

def save_response(filename, data):
    if not SAVE_RESPONSES:
        return
    safe_name = filename.replace("/", "_").replace("?", "_")
    path = os.path.join(LOG_DIR, safe_name)
    with open(path, "w") as f:
        if isinstance(data, (dict, list)):
            json.dump(data, f, indent=2)
        else:
            f.write(str(data))

async def call(client, method, url, label=None, **kwargs):
    full_url = BASE_URL + url
    label = label or f"{method.upper()} {url}"
    print(f"\n {label}")
    start = time.time()
    try:
        response = await getattr(client, method.lower())(full_url, **kwargs)
    except Exception as e:
        print(f"Request failed: {e}")
        save_response(f"{url}_{method}_error.txt", str(e))
        return {}, 0.0

    duration = round(time.time() - start, 4)
    print(f"Time: {duration}s | Status: {response.status_code}")

    try:
        data = response.json() if isinstance(response, httpx.Response) else {}
        if asyncio.iscoroutine(data):
            data = await data
        print("Response:", data.get("message") or data.get("detail") or "...")
        save_response(f"{url}_{method}.json", data)
    except Exception as e:
        print("Failed to parse JSON:", e)
        save_response(f"{url}_{method}_raw.txt", response.text)
        data = {}

    return data, duration

async def test_api(fake_count: int):
    async with httpx.AsyncClient() as client:
        await call(client, "GET", "/")
        # await call(client, "DELETE", "/deletetasks")

        # Retry logic for fake task creation
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            print(f"\n Attempt {attempt} to create {fake_count} fake tasks")
            create_resp, _ = await call(client, "POST", f"/tasks/fake/{fake_count}")
            created_count = create_resp.get("count", 0)

            if created_count == fake_count:
                print(f"Successfully created {created_count} tasks.")
                break
            elif attempt < max_retries:
                print(f"Only {created_count} tasks created. Retrying...")
                await asyncio.sleep(1)
            else:
                print(f"Gave up after {max_retries} attempts. Created {created_count} tasks.")

        
        await asyncio.sleep(2)

        
        all_tasks_resp, t1 = await call(client, "GET", "/alltasks", label="GET /tasks (1st - Cold)")
        actual_count = all_tasks_resp.get("count", 0)
        print(f"\n Expected: {fake_count}, Found in DB: {actual_count}")

       
        _, t2 = await call(client, "GET", "/alltasks", label="GET /tasks (2nd - Cached?)")
        print(f"\n Cache test: Cold = {t1}s, Cached = {t2}s, time difference = {round(t1 - t2, 4)}s")

        tasks = all_tasks_resp.get("tasks", [])
        if not tasks:
            print("No tasks found in DB.")
            return

        
        new_task_data, _ = await call(client, "POST", "/addtasks", json=random_task())
        new_task_id = new_task_data.get("task", {}).get("id", "")
        existing_id = tasks[0].get("id", "")

        if existing_id:
            await call(client, "PUT", f"/updatetasks/{existing_id}", json={"title": "Updated Title"})
            await call(client, "DELETE", f"/deletetask/{existing_id}")
        if new_task_id:
            await call(client, "DELETE", f"/deletetask/{new_task_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Task API routes")
    parser.add_argument("--fake", type=int, default=10, help="Number of fake tasks to generate")
    args = parser.parse_args()

    prepare_logs()
    print(f"Starting Task API Route Test with {args.fake} fake tasks")
    start = time.time()
    asyncio.run(test_api(args.fake))
    print(f"\n Completed in {round(time.time() - start, 2)} seconds")
