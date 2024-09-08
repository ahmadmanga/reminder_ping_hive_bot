from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

# Load MongoDB connection details from environment variables
MONGO_URI = os.getenv('MONGO_URI')
DATABASE_NAME = 'reminder_bot'
COLLECTION_NAME = 'blocks'

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

def load_last_block():
    """Load the last processed block number from MongoDB."""
    doc = collection.find_one({'_id': 'last_block'})
    if doc:
        return doc.get('block_num')
    return None

def save_last_block(block_num):
    """Save the last processed block number to MongoDB."""
    collection.update_one(
        {'_id': 'last_block'},
        {'$set': {'block_num': block_num}},
        upsert=True
    )

