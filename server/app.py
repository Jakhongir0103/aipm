import base64
import os
import time

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = os.environ["SECRET_TOKEN_ENCRYPTION_KEY"]
fernet = Fernet(SECRET_KEY.encode())

TOKEN_TIME_TO_LIVE_SECONDS = 90


@app.get("/generate-token")
async def generate_token():
    try:
        timestamp = int(time.time())  # Current timestamp in seconds
        deadline_timestamp = timestamp + TOKEN_TIME_TO_LIVE_SECONDS

        # Convert timestamp to bytes and encrypt
        timestamp_bytes = str(deadline_timestamp).encode()
        encrypted_timestamp = fernet.encrypt(timestamp_bytes)

        # Convert to base64 for URL-safe string
        token = base64.urlsafe_b64encode(encrypted_timestamp).decode()

        return {"token": token, "timestamp": timestamp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
