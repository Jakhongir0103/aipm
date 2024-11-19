import os

from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()
db_password = os.environ["MONGO_SECRET"]

uri = f"mongodb+srv://saidaliyevjahongir:{db_password}@cluster0.jwhlb.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi("1"))
db = client["AIPM"]

user_points = db["user_points"]
user_transactions = db["user_transactions"]

# Send a ping to confirm a successful connection
try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
