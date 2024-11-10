from fastapi import FastAPI, Request
from fastapi.responses import FileResponse

import requests
from dotenv import load_dotenv
import os
from typing import List

from utils import (
    send_message,
    get_todays_date,
    generate_qr_code
)
from db import (
    transactions_collection,
    redemptions_collection
)

load_dotenv()

app = FastAPI()

threshold = 2 # number of transactions for discount

@app.get("/static/qr_codes/{file_name}")
async def index(file_name: str):
    return FileResponse(f'./qr_codes/{file_name}')

@app.post("/message")
async def reply(request: Request):
    twilio_request = await request.form()

    # prepare a message
    # print(twilio_request)
    message_body = twilio_request.get('Body').strip()
    message_profile_name = twilio_request.get('ProfileName').strip()
    message_whatsapp_number = twilio_request.get("From").replace("whatsapp:","")

    todays_date = get_todays_date()
    
    # save into database
    user_query = {'whatsapp_number': message_whatsapp_number}
    user_transactions_num = transactions_collection.count_documents(user_query)

    if user_transactions_num + 1 >= threshold:
        # message
        qr_image_path = generate_qr_code(whatsapp_number=message_whatsapp_number)
        message = f"Congratulations! 🎉 You've earned {threshold} loyalty points and a free coffee! ☕ Simply show this QR code at the counter to claim your coffee. Your points have been reset, so you can start earning again!"

        # reset for transactions
        transactions_collection.delete_many(user_query)

        # reset for transactions
        user_transaction = {"whatsapp_number":message_whatsapp_number, "status":todays_date}
        redemptions_collection.insert_one(user_transaction)

        send_message(
            to_number=message_whatsapp_number,
            text=message,
            media_path=qr_image_path
        )
    else:
        # message
        message = f"Thank you for your purchase! 🎉 You've just earned a loyalty point. You now have {user_transactions_num+1}/{threshold} points. Keep going — when you reach {threshold} points, you'll get a free coffee on us! ☕"

        # update
        user_transaction = {"whatsapp_number":message_whatsapp_number, "date":todays_date}
        transactions_collection.insert_one(user_transaction)

        send_message(
            to_number=message_whatsapp_number,
            text=message
        )