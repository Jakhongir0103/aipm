import time

from dotenv import load_dotenv
from encrypt_token import encrypt_timestamp
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


TOKEN_TIME_TO_LIVE_SECONDS = 90


@app.get("/generate-token")
async def generate_token():
    try:
        timestamp = int(time.time())
        deadline_timestamp = timestamp + TOKEN_TIME_TO_LIVE_SECONDS

        token = encrypt_timestamp(deadline_timestamp)

        return {"token": token, "timestamp": timestamp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
