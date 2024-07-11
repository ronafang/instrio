from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import random
import boto3
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests

app = FastAPI()

# Allow CORS for localhost:8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "https://instr.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# S3 Configuration
s3_bucket_name = "instrio-gpus"
s3_file_key = "gpus.txt"
local_file_path = "gpus.txt"

# Initialize the S3 client
s3_client = boto3.client('s3')

# List of host:port strings
host_port_list = []

@app.get("/models")
def models():
    return "".join(host_port_list)
@app.put("/convert")
async def convert(request: Request):
    global host_port_list
    if not host_port_list:
        raise HTTPException(status_code=500, detail="No gpus available")
    
    # Randomly select a host:port from the list
    selected_host_port = random.choice(host_port_list)
    
    # Construct the URL
    url = f"{selected_host_port}/convert"
    print(f"Forwarding request to: {url}")

    try:
        # Forward the request to the selected host and get the response
        headers = dict(request.headers)
        body = await request.body()
        response = requests.put(url, headers=headers, data=body)
        # Return the response
        return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))


    except requests.RequestException as exc:
        print(f"Request error occurred: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


async def pull_file_from_s3():
    try:
        print("pulling")
        s3_client.download_file(s3_bucket_name, s3_file_key, local_file_path)        
        with open(local_file_path, 'r') as file:
            global host_port_list
            host_port_list = [line.strip() for line in file.readlines()]
    except Exception as e:
        print(f"Failed to download file from S3: {e}")

def start_scheduler():
    print("started")
    scheduler = AsyncIOScheduler()
    scheduler.add_job(pull_file_from_s3, 'interval', seconds=120)
    scheduler.start()

@app.on_event("startup")
async def startup_event():
    await pull_file_from_s3()
    start_scheduler()
