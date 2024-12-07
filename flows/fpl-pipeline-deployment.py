import os
import requests
import json
from datetime import timedelta
from prefect import flow, task
from prefect.tasks import task_input_hash
from prefect.utilities.filesystem import Files
from typing import Tuple
import pendulum
from prefect.filesystems import LocalFileSystem

# get secrets - in Prefect you might want to use blocks for these
MINIO_ENDPOINT_FPL = os.getenv("MINIO_ENDPOINT_FPL")
MINIO_ACCESS_KEY_FPL = os.getenv("MINIO_ACCESS_KEY_FPL")
MINIO_SECRET_KEY_FPL = os.getenv("MINIO_SECRET_KEY_FPL")

PG_HOST_FPL = os.getenv("PG_HOST_FPL")
PG_PORT_FPL = os.getenv("PG_PORT_FPL")
PG_USER_FPL = os.getenv("PG_USER_FPL")
PG_PASSWORD_FPL = os.getenv("PG_PASSWORD_FPL")
PG_DATABASE_FPL = os.getenv("PG_DATABASE_FPL")
PG_TABLE_NAME_GW_FPL = os.getenv("PG_TABLE_NAME_GW_FPL")
PG_TABLE_NAME_FIXTURES_FPL = os.getenv("PG_TABLE_NAME_FIXTURES_FPL")

@task(retries=1, cache_key_fn=task_input_hash, cache_expiration=timedelta(hours=1))
def download_file(url: str, file_path: str) -> str:
    """Download a file from a URL and save it locally."""
    response = requests.get(url)
    response.raise_for_status()
    
    with open(file_path, "wb") as f:
        f.write(response.content)
    
    return file_path

@task(retries=1)
def upload_file_to_fastapi(endpoint: str, source: str, file_path: str, filename: str) -> None:
    """Upload a file to FastAPI using multipart/form-data."""
    url = f"http://os8w0ss0c4kwoogk8o44csg4.65.108.88.160.sslip.io/upload/{source}"
    with open(file_path, "rb") as f:
        files = {"file": (filename, f)}
        response = requests.post(url, files=files)
        response.raise_for_status()
        
        if response.status_code != 200:
            raise Exception(f"Failed to upload {filename}. Status Code: {response.status_code}")

@task(retries=1)
def ingest_to_postgres(source: str) -> None:
    """Trigger data ingestion to PostgreSQL."""
    url = "http://os8w0ss0c4kwoogk8o44csg4.65.108.88.160.sslip.io/ingest/" + source
    headers = {"Content-Type": "application/json"}
    data = {"source": source}
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    
    if response.status_code != 200:
        raise Exception(f"Failed to ingest {source}. Status Code: {response.status_code}")

@flow(name="fpl_data_pipeline", retries=1)
def fpl_pipeline():
    """Main flow for FPL data pipeline."""
    # Define file paths and URLs
    url_gw = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2024-25/gws/merged_gw.csv"
    url_fixtures = "https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2024-25/fixtures.csv"
    
    gw_file_path = "/tmp/merged_gw_24_25.csv"
    fixtures_file_path = "/tmp/fixtures_24_25.csv"

    # Download files
    gw_path = download_file(url_gw, gw_file_path)
    fixtures_path = download_file(url_fixtures, fixtures_file_path)

    # Upload to Minio via FastAPI
    upload_file_to_fastapi("/upload", "gameweeks", gw_path, "merged_gw_24_25.csv")
    upload_file_to_fastapi("/upload", "fixtures", fixtures_path, "fixtures_24_25.csv")

    # Ingest to PostgreSQL
    ingest_to_postgres("gameweeks")
    ingest_to_postgres("fixtures")

if __name__ == "__main__":
    # For local testingn
    fpl_pipeline()