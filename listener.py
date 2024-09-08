import requests
import time
from datetime import datetime
import re
from beem import Hive
from pymongo import MongoClient
import os
from dotenv import load_dotenv

SLEEP_INTERVAL = 30
HIVE_API = 'https://api.hive.blog'
hive = Hive()

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv('MONGO_URI')

# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client['reminder_bot']  # Database name
blacklist_collection = db['blacklist']  # Blacklist collection

def get_latest_block_num():
    """Get the latest block number from the HIVE blockchain."""
    data = {
        "jsonrpc": "2.0",
        "method": "condenser_api.get_dynamic_global_properties",
        "params": [],
        "id": 1
    }
    retries = 10
    while retries > 0:
        try:
            response = requests.post(HIVE_API, json=data).json()
            result = response.get('result')
            if result:
                return result['head_block_number']
            else:
                print("Failed to get latest block number. Retrying...")
                time.sleep(SLEEP_INTERVAL / 10)
                retries -= 1
        except Exception as e:
            print(f"Exception while fetching latest block number: {e}")
            time.sleep(SLEEP_INTERVAL / 10)
            retries -= 1

    print("Max retries exceeded. Aborting.")
    raise Exception("Failed to fetch latest block number after multiple retries.")

def get_block_range(start_block, end_block):
    """Fetch a range of blocks from the HIVE blockchain using block_api.get_block_range."""
    
    if start_block == end_block:
        print(f"Waiting for more blocks before fetching...")
        time.sleep(SLEEP_INTERVAL)
    
    data = {
        "jsonrpc": "2.0",
        "method": "block_api.get_block_range",
        "params": {
            "starting_block_num": start_block,
            "count": end_block - start_block + 1
        },
        "id": 1
    }
    retries = 10
    while retries > 0:
        try:
            response = requests.post(HIVE_API, json=data).json()
            result = response.get('result')
            if result['blocks']:
                print(f"Fetched block range {start_block} to {end_block}")
                return result['blocks']
            else:
                print(f"Failed to fetch block range {start_block} to {end_block}. Retrying...")
                time.sleep(SLEEP_INTERVAL)
                retries -= 1
        except Exception as e:
            print(f"Exception while fetching block range {start_block} to {end_block}: {e}")
            time.sleep(SLEEP_INTERVAL)
            retries -= 1

    print("Max retries exceeded. Aborting.")
    raise Exception("Failed to fetch block data after multiple retries.")

def listen_for_comments(start_block, end_block, blacklist):
    """Listen for comments in a range of blocks and process them."""
    blocks = get_block_range(start_block, end_block)
    for block in blocks:
        block_timestamp = block['timestamp']  # Use timestamp directly
        for transaction in block['transactions']:
            for operation in transaction['operations']:
                if operation['type'] == 'comment_operation':
                    comment_data = operation['value']
                    if comment_data['parent_author'] != '':
                        comment = {
                            'author': comment_data['author'],
                            'permlink': comment_data['permlink'],
                            'parent_author': comment_data['parent_author'],
                            'parent_permlink': comment_data['parent_permlink'],
                            'body': comment_data['body'],
                            'metadata': comment_data["json_metadata"],
                            'block_timestamp': block_timestamp
                        }
                        if comment['author'] not in blacklist:
                            yield comment
                        else:
                            print(f"Blacklisted user: {comment['author']}")

def load_blacklist():
    """Load the blacklist of users from MongoDB."""
    blacklist = set()
    try:
        # Fetch the blacklist from MongoDB
        blacklist_docs = blacklist_collection.find()
        for doc in blacklist_docs:
            blacklist.add(doc['username'])  # Assuming your MongoDB documents have a 'username' field
    except Exception as e:
        print(f"Error loading blacklist from MongoDB: {e}")
    return blacklist

