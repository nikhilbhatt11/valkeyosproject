from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime,timezone
from opensearch_client import os_client
from valkey_client import valkey_client
import time
import json
from fastapi.middleware.cors import CORSMiddleware
from opensearchpy.helpers import bulk
from fastapi import Query


from fake_data import generate_fake_tasks

origins = [
    "http://localhost:5173", 
   
]



app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,         
    allow_credentials=True,
    allow_methods=["*"],          
    allow_headers=["*"],           
)



class Task(BaseModel):
    title: str
    description: str
    status: str = "pending"
    deadline: str  
    

@app.get("/")
def read_root():
    return {"message": "Task Management API is running"}







@app.post("/addtasks")
async def create_task(task: Task):
    print("Task is running 000000")
    print("Received task:", task.model_dump())

    try:
        
        task_data = {
            **task.model_dump(),
            "createdAt": datetime.now(timezone.utc).isoformat()
        }

        
        response = os_client.index(index="tasks", body=task_data)
        task_id = response["_id"]
        task_data["id"] = task_id

        print("New task creation data:", task_data)

        
        valkey_client.set(f"tasks:{task_id}", json.dumps(task_data), ex=60)

        
        first_page_keys = valkey_client.keys("tasks:all:page:1:limit:*")
        for key in first_page_keys:
            cached_data = valkey_client.get(key)
            if cached_data:
                tasks = json.loads(cached_data)
                limit = int(key.split(":")[-1])
                
                
                tasks = [task_data] + tasks
                tasks = tasks[:limit]

                valkey_client.set(key, json.dumps(tasks), ex=60)

        
        current_count = valkey_client.get("tasks:count")
        if current_count:
            valkey_client.set("tasks:count", int(current_count) + 1, ex=60)

        return {"message": "Task created", "task": task_data}

    except Exception as err:
        print("Error in create_task:", err)
        raise HTTPException(status_code=500, detail="Failed to create task")









@app.get("/alltasks")
async def get_all_tasks(page: int = Query(1, ge=1), limit: int = Query(1000, ge=1, le=10000)):

    cache_key = f"tasks:all:page:{page}:limit:{limit}"

    try:
        start_time = time.time()

        cached = valkey_client.get(cache_key)
        
        if cached:
            print("cached data is loading")
            tasks = json.loads(cached)
            total_count = valkey_client.get("tasks:count")
            return {
                "tasks": tasks,
                "count": int(total_count) if total_count else len(tasks)
            }

        from_ = (page - 1) * limit

        result = os_client.search(
            index="tasks",
            body={
                "from": from_,
                "size": limit,
                "query": {
                    "match_all": {}
                }
            }
        )

        hits = result["hits"]["hits"]
        total_count = result["hits"]["total"]["value"]

        tasks = [{**hit["_source"], "id": hit["_id"]} for hit in hits]

        valkey_client.set(cache_key, json.dumps(tasks), ex=60)
        
        
        return {
            "tasks": tasks,
            "count": total_count
        }

    except Exception as err:
        print("Error in get_all_tasks:", err)
        raise HTTPException(status_code=500, detail="Something went wrong")





class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    deadline:str | None = None




        







@app.put("/updatetasks/{task_id}")
async def update_task(task_id: str, task_update: TaskUpdate):
    try:
        
        existing_doc = os_client.get(index="tasks", id=task_id)
        if not existing_doc.get("found"):
            raise HTTPException(status_code=404, detail="Task not found")

       
        updated_data = {
            **task_update.model_dump(),
            "createdAt": existing_doc["_source"]["createdAt"]
        }

        
        updatedtask = os_client.index(index="tasks", id=task_id, body=updated_data)
        print(updatedtask)

        
        valkey_client.set(
            f"tasks:{task_id}",
            json.dumps({**updated_data, "id": task_id}),
            ex=60
        )

        
        paginated_keys = valkey_client.keys("tasks:all:page:*:limit:*")
        for key in paginated_keys:
            cached_page = valkey_client.get(key)
            if cached_page:
                tasks = json.loads(cached_page)
                updated = False
                for i, task in enumerate(tasks):
                    if task["id"] == task_id:
                        tasks[i] = {**updated_data, "id": task_id}
                        updated = True
                        break
                if updated:
                    valkey_client.set(key, json.dumps(tasks), ex=60)

        return {
            "message": "Task updated",
            "task": {**updated_data, "id": task_id}
        }

    except Exception as e:
        print("Error in update_task:", e)
        raise HTTPException(status_code=500, detail="Failed to update task")









@app.post("/tasks/fake/{count}")
async def create_fake_tasks(count: int):
    try:
        fake_tasks = generate_fake_tasks(count)
        now = datetime.now(timezone.utc).isoformat()

        
        actions = [
            {
                "_index": "tasks",
                "_source": {**task, "createdAt": now}
            }
            for task in fake_tasks
        ]

        db_start = time.time()
        success, _ = bulk(os_client, actions)
        db_end = time.time()

        
        cache_write_time = None
        if success:
            tasks_to_return = [{**a["_source"]} for a in actions]
           
            existing_all = valkey_client.get("tasks:all")
            if existing_all:
                cache_start = time.time()
                all_tasks = json.loads(existing_all)
                all_tasks.extend(tasks_to_return)
                valkey_client.set("tasks:all", json.dumps(all_tasks), ex=60)

                for task in tasks_to_return:
                   
                    cache_key = f"tasks:{task['title']}" 
                    valkey_client.set(cache_key, json.dumps(task), ex=60)
                cache_end = time.time()
                cache_write_time = round(cache_end - cache_start, 4)

        return {
            "message": f"Requested: {count} | Successfully created: {success}",
            "db_write_time_sec": round(db_end - db_start, 4),
            "cache_write_time_sec": cache_write_time,
            "count": success
        }

    except Exception as e:
        print("Error in create_fake_tasks:", e)
        raise HTTPException(status_code=500, detail="Failed to generate fake tasks")

    

@app.delete("/deletetask/{task_id}")
async def delete_task(task_id: str):
    try:
        
        os_response = os_client.delete(index="tasks", id=task_id, ignore=[404])
        if os_response["result"] != "deleted":
            raise HTTPException(status_code=404, detail=f"Task with id '{task_id}' not found.")

        
        valkey_client.delete(f"tasks:{task_id}")

        
        paginated_keys = valkey_client.keys("tasks:all:page:*:limit:*")
        for key in paginated_keys:
            cached_page = valkey_client.get(key)
            if cached_page:
                tasks = json.loads(cached_page)
                new_tasks = [task for task in tasks if task.get("id") != task_id]
                if len(new_tasks) != len(tasks):  
                    valkey_client.set(key, json.dumps(new_tasks), ex=60)

        
        total_count = valkey_client.get("tasks:count")
        if total_count:
            valkey_client.set("tasks:count", int(total_count) - 1, ex=60)

        return {"message": f"Task with id '{task_id}' deleted successfully."}

    except HTTPException:
        raise
    except Exception as e:
        print("Error deleting task:", e)
        raise HTTPException(status_code=500, detail="Failed to delete task")





#@app.delete("/deletetasks")
# async def delete_all_tasks():
#     try:
        
#         query = {
#             "query": {
#                 "match_all": {}
#             }
#         }
#         os_response = os_client.delete_by_query(index="tasks", body=query)

#         # Delete main cache and paginated caches from Valkey
#         keys = valkey_client.keys("tasks:all*")
#         if keys:
#             valkey_client.delete(*keys)

#         return {"message": "All tasks deleted", "opensearch_result": os_response}

#     except Exception as e:
#         print("Error deleting all tasks:", e)
#         raise HTTPException(status_code=500, detail="Failed to delete all tasks")