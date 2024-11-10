from datetime import datetime

import logging
from twilio.rest import Client
from dotenv import load_dotenv

# from db import fs

import qrcode
import os

import boto3

load_dotenv()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv('TWILIO_NUMBER')
bucket_name = os.getenv("BUCKET_NAME")
client = Client(account_sid, auth_token)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_message(to_number, text, media_path=None):
    try:
        message = client.messages.create(
            body=text,
            from_=f"whatsapp:{twilio_number}",
            to=f"whatsapp:{to_number}"
        )
        if media_path is not None:
            message = client.messages.create(
                media_url=[media_path],
                from_=f"whatsapp:{twilio_number}",
                to=f"whatsapp:{to_number}"
            )
        logger.info(f"Message sent to {to_number}: {message.body}")
    except Exception as e:
        logger.error(f"Error sending message to {to_number}: {e}")

def get_todays_date():
    """
    attributs:
    today_date.year
    today_date.month
    today_date.weekday()
    today_date.day
    today_date.hour
    today_date.minute
    today_date.second

    today_date.strftime('%Y-%m-%d %H:%M:%S')
    """
    todays_date = datetime.today()
    return todays_date

def generate_qr_code(whatsapp_number):
    """Create a QR code and uploads it into MongoDB GridFS. Returns the uploaded QR code id."""
    # create a QR code from the unique identifier
    qr = qrcode.QRCode(
        version=1,  # Size of the QR code
        error_correction=qrcode.constants.ERROR_CORRECT_L,  # Error correction level
        box_size=10,  # Size of each box in the QR code grid
        border=4,  # Border size around the QR code
    )

    qr.add_data(whatsapp_number)
    qr.make(fit=True)

    # create an image of the QR code
    qr_image = qr.make_image(fill="black", back_color="white")

    # Save the QR code as an image file at ./qr_codes/
    todays_date = get_todays_date()
    qr_image_name = f"{whatsapp_number.replace("+","")}-{todays_date.strftime('%Y-%m-%d-%H-%M-%S')}.png"
    qr_image_path = os.path.join("qr_codes", qr_image_name)
    qr_image.save(qr_image_path)

    # TODO: upload the image on online public host, and get the url
    # # Upload the local image to AWS S3 client
    # s3 = boto3.client('s3')
    # s3.upload_file(qr_image_path, bucket_name, qr_image_name, ExtraArgs={'ACL': 'public-read'})

    # qr_image_url = f"https://{bucket_name}.s3.amazonaws.com/{qr_image_name}"
    qr_image_url = "https://images.unsplash.com/photo-1545093149-618ce3bcf49d?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=668&q=80"

    print('Image url:', qr_image_url)

    return qr_image_url