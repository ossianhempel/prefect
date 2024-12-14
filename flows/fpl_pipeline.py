import datetime
import pendulum
import os
import requests
import json
from prefect import flow, task

# get secrets
# MINIO_ENDPOINT_FPL = os.getenv("MINIO_ENDPOINT_FPL")
# MINIO_ACCESS_KEY_FPL = os.getenv("MINIO_ACCESS_KEY_FPL")
# MINIO_SECRET_KEY_FPL = os.getenv("MINIO_SECRET_KEY_FPL")

# PG_HOST_FPL = os.getenv("PG_HOST_FPL")
# PG_PORT_FPL = os.getenv("PG_PORT_FPL")
# PG_USER_FPL = os.getenv("PG_USER_FPL")
# PG_PASSWORD_FPL = os.getenv("PG_PASSWORD_FPL")
# PG_DATABASE_FPL = os.getenv("PG_DATABASE_FPL")
# PG_TABLE_NAME_GW_FPL = os.getenv("PG_TABLE_NAME_GW_FPL")
# PG_TABLE_NAME_FIXTURES_FPL = os.getenv("PG_TABLE_NAME_FIXTURES_FPL")

WEB_SERVER_URL = "http://ckwcgcscsok4w0w84w0s80ww.65.108.88.160.sslip.io"

@task
def download_file(url: str, file_path: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    with open(file_path, "wb") as f:
        f.write(response.content)
    return file_path

@task
def upload_file_to_fastapi(endpoint: str, source: str, file_path: str, filename: str) -> None:
    url = f"{WEB_SERVER_URL}/upload/{source}"
    with open(file_path, "rb") as f:
        files = {"file": (filename, f)}
        response = requests.post(url, files=files)
        response.raise_for_status()
        if response.status_code != 200:
            raise Exception(f"Failed to upload {filename}. Status Code: {response.status_code}")

@task
def ingest_to_postgres(source: str) -> None:
    url = f"{WEB_SERVER_URL}/ingest/{source}"
    headers = {"Content-Type": "application/json"}
    data = {"source": source}
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    if response.status_code != 200:
        raise Exception(f"Failed to ingest {source}. Status Code: {response.status_code}")

@flow(name="fpl_data_pipeline")
def fpl_pipeline():
    # URLs and file paths
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
    fpl_pipeline()