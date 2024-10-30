from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
import time
import random
import boto3
import httpx
import datetime
import shopify
from cachetools import cached, TTLCache
from apscheduler.schedulers.asyncio import AsyncIOScheduler


API_TOKEN = 'REMOVED'
SHOP_URL = '733ea1-7d.myshopify.com'
API_VERSION = '2024-07'

shop_url = f"https://{SHOP_URL}/admin/api/{API_VERSION}"
shopify.Session.setup(api_key="", secret="")

session = shopify.Session(SHOP_URL, API_VERSION, API_TOKEN)
shopify.ShopifyResource.activate_session(session)

has_valid_purchase = defaultdict(lambda: False)

cache = TTLCache(maxsize=100, ttl=3600)

def has_valid_purchase_in_past_month(customer_id: str) -> bool:
    now = datetime.datetime.now()
    month_ago = now - datetime.timedelta(days=31)
    
    orders = shopify.Order.find(customer_id=customer_id, created_at_min=month_ago.isoformat())

    for order in orders:
        if order.customer and str(order.customer.id) == str(customer_id) and order.cancelled_at is None:
            return True
    return False

@cached(cache)
def is_valid_user(customer_id: str, email: str) -> bool:
    try:
        email_search_results = shopify.Customer.find(email=email)
        customer = email_search_results[0] if email_search_results else None

        if customer and str(customer.id) == str(customer_id):
            return True
        else:
            return False
    except Exception as e:
        print(f"Error while checking user validity: {e}")
        return False

app = FastAPI()

# Allow CORS for localhost:8000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "https://instr.io", "chrome-extension://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# S3 Configuration
s3_bucket_name = "instrio-gpus"
s3_file_key = "gpus.txt"
local_file_path = "gpus.txt"

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

table = dynamodb.Table('seconds_listened')


host_port_list = []

def get_seconds_listened(user):
    response = table.get_item(Key={'user': user})
    if 'Item' in response:
        return response['Item'].get('seconds', 0)
    return 0
    
def add_seconds(user, seconds_to_add):
    table.update_item(
        Key={'user': user},
        UpdateExpression="SET seconds = if_not_exists(seconds, :start) + :inc",
        ExpressionAttributeValues={
            ':inc': seconds_to_add,
            ':start': 0
        }
    )

last_request_time = defaultdict(lambda: 0)  # Stores the last request time in seconds

def is_not_too_soon(customer_id: str) -> bool:
    current_time = time.time()
    last_time = last_request_time[customer_id]

    # Check if the request is made within 3 seconds of the last one
    if current_time - last_time < 3:
        return True  # Too soon
    else:
        last_request_time[customer_id] = current_time
        return False  # Not too soon

@app.put("/convert")
async def convert(request: Request):
    global host_port_list
    if not host_port_list:
        raise HTTPException(status_code=500, detail="No gpus available")
    
    selected_host_port = random.choice(host_port_list)
    url = f"{selected_host_port}/convert"
    print(f"Forwarding request to: {url}")

    try:
        headers = dict(request.headers)
        form = await request.form()
        customer_id = form.get("user")
        email = form.get("email")

        if not is_valid_user(customer_id, email):
            raise HTTPException(status_code=403, detail="Invalid account.")

        # Check if the request is made too soon
        if is_not_too_soon(customer_id):
            raise HTTPException(status_code=429, detail="Too many requests. Please wait a few seconds.")

        file = form.get("file")

        if not has_valid_purchase[customer_id]:
            if has_valid_purchase_in_past_month(customer_id):
                has_valid_purchase[customer_id] = True

        if has_valid_purchase[customer_id] or (get_seconds_listened(customer_id) < 30 * 60):
            if random.randint(0, 100) <= 1:
                has_valid_purchase[customer_id] = False
            file_content = await file.read()

            files = {
                "file": (file.filename, file_content, file.content_type)
            }
            data = {
                "user": customer_id
            }

            async with httpx.AsyncClient() as client:
                add_seconds(customer_id, 5)
                response = await client.put(url, data=data, files=files)
                return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers))
        
        raise HTTPException(status_code=400, detail="Please subscribe!")

    except httpx.RequestError as exc:
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
