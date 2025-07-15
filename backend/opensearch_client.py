
from dotenv import load_dotenv
import os
from opensearchpy import OpenSearch

load_dotenv()

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL")

os_client = OpenSearch(OPENSEARCH_URL)

