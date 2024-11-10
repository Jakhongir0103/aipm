
# import gridfs
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from dotenv import load_dotenv
import os

load_dotenv()
db_password = os.environ.get('MONGO_SECRET')

uri = f"mongodb+srv://saidaliyevjahongir:{db_password}@cluster0.jwhlb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["AIPM"]

# fs = gridfs.GridFS(db)

transactions_collection = db["transactions"] # ['whatsapp_number', 'date']
redemptions_collection = db["redemptions"] # ['whatsapp_number', 'status']

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)