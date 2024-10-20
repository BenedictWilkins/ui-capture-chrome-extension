"""FastAPI server for capturing web UI data.

This is the end point for browser extensions.
It must be running if the extension is going to be capturing data.

Run with:
```
uvicorn webuicapture.serve:app --reload --port 7659
```
after installing webuicapture with pip.
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from .data import CaptureData
from typing import Any
import time
import json

app = FastAPI()

# only allow requests from localhost
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost", "http://127.0.0.1"],  # Allow only localhost
    allow_origins=["*"],  # Allow all origins, TODO this may be a security risk...
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)
from pydantic import BaseModel


class PingMessage(BaseModel):
    message: str


@app.post("/ping")
async def ping(request: Request, message: PingMessage):
    """Endpoint for testing server connection."""
    origin = request.headers.get("origin")
    print(f"{time.time()}, PING: {message}, origin: {origin}")
    return {"message": message}


INDEX = 0


@app.post("/upload")
async def upload_data(request: Request):
    global INDEX
    """Endpoint for uploading capture data from browser extensions."""
    # The raw request is needed here to prevent fastapi validation errors... (some issue with json serialization schema)
    try:
        data = CaptureData.model_validate_json(await request.body(), context={})
        data.save_to_json("./dataset/", f"{INDEX}")
        INDEX += 1
        return {}  # success!
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
