from fastapi import FastAPI, Request, Response, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import threading
import asyncio
from datetime import datetime
from process import process
from io import BytesIO
import time

app = FastAPI()

threads = []
count = 0
visits = 0
origins = ["*"]

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

def process_audio(audio_data, output_list, stop_event):
    output = process(audio_data)
    if not stop_event.is_set():
        output_list.append(output)

@app.put("/convert")
async def convert(file: UploadFile):
    global count
    count += 1
    if file.content_type == 'audio/ogg':
        audio_data = BytesIO(await file.read())
        output_list = []
        stop_event = threading.Event()
        thread = threading.Thread(target=process_audio, args=(audio_data, output_list, stop_event))
        threads.append((thread, stop_event))
        thread.start()

        thread.join(timeout=40)
        if thread.is_alive():
            stop_event.set()
            print(f"Thread timed out: {thread.name}")
            return Response(status_code=504, content="Processing timed out")

        if count % 5 == 0:
            print(count, datetime.now())

        if output_list:
            output = output_list[0]
            return Response(content=output.getvalue(), media_type='audio/ogg', headers={
                'Content-Disposition': 'attachment; filename="audio.ogg"'
            })

    return Response(status_code=400, content="Invalid file type")
