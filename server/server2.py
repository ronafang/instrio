from fastapi import FastAPI, Request, Response, UploadFile
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from process import process
from io import BytesIO
import os

app = FastAPI()

origins = [
    "http://localhost:3299",
    "https://cdn.jsdelivr.net",
    "https://cdn.webrtc-experiment.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


with open("index.html", "r") as file:
    html_content = file.read()

with open("RecordRTC.js", "r") as file:
    rtc = file.read()

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers['Cross-Origin-Opener-Policy'] = 'same-origin'
    response.headers['Cross-Origin-Embedder-Policy'] = 'require-corp'
    return response

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/RecordRTC.js", response_class=HTMLResponse)
async def read_index():
    return HTMLResponse(content=rtc, status_code=200)


@app.put("/convert")
async def convert(file: UploadFile):
    if file.content_type == 'audio/ogg':
        audio_data = BytesIO(await file.read())
        output = process(audio_data)
        return Response(content=output.getvalue(), media_type='audio/ogg', headers={
            'Content-Disposition': 'attachment; filename="audio.ogg"'
        })
    return Response(status_code=400, content="Invalid file type")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3299)
