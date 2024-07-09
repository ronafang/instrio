from fastapi import FastAPI, Request, Response, UploadFile, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from process import process
from io import BytesIO
import os
import uvicorn
from concurrent.futures import ThreadPoolExecutor
import asyncio
from  datetime import datetime
app = FastAPI()

executor = ThreadPoolExecutor(max_workers=100)
count = 0
visits = 0
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


with open("index.html", "r") as file:
    index_html = file.read()

with open("RecordRTC.js", "r") as file:
    rtc = file.read()

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
    return response

@app.get("/", response_class=HTMLResponse)
async def home():
    global visits
    print(count, visits, "at", datetime.now())
    return HTMLResponse(content=index_html, status_code=200)

@app.get("/RecordRTC.js", response_class=HTMLResponse)
async def read_index():
    return HTMLResponse(content=rtc, status_code=200)


@app.put("/convert")
async def convert(file: UploadFile):
    global count
    count  += 1
    if file.content_type == 'audio/ogg':
        audio_data = BytesIO(await file.read())
        loop = asyncio.get_running_loop()
        output = await loop.run_in_executor(executor, process, audio_data)
        if (count % 5 == 0):
            print(count, datetime.now())
        return Response(content=output.getvalue(), media_type='audio/ogg', headers={
            'Content-Disposition': 'attachment; filename="audio.ogg"'
        })
    return Response(status_code=400, content="Invalid file type")
