from dotenv import load_dotenv
import os

load_dotenv()  


import redis


VALKEY_HOST = os.getenv("VALKEY_HOST")
VALKEY_PORT = int(os.getenv("VALKEY_PORT"))

try:
    valkey_client = redis.Redis(host=VALKEY_HOST, port=VALKEY_PORT, decode_responses=True)
    valkey_client.ping()
    print("Valkey connected successfully")
except redis.ConnectionError as err:
    print("Valkey connection error:", err)

