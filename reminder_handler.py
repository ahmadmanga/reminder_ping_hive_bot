import os
import time
import random
from datetime import datetime, timedelta
from dateutil import parser
from dotenv import load_dotenv
from pymongo import MongoClient, errors
from beem import Hive
from beem.comment import Comment
from beem.exceptions import ContentDoesNotExistsException

# Load environment variables
load_dotenv()

HIVE_USER = os.getenv('HIVE_USERNAME')
HIVE_POSTING_KEY = os.getenv('POSTING_KEY')
MONGO_URI = os.getenv('MONGO_URI')
DEFAULT_REMIND_NOTIFICATION = "Attention @{author}!! Here's your reminder to check back on this conversation!"
DEFAULT_FOOTER = ""

# List of Hive API nodes
HIVE_API_NODES = [
    'https://api.hive.blog',
    'https://api.deathwing.me',
    'https://api.openhive.network'


# Initialize MongoDB client
client = MongoClient(MONGO_URI)
db = client['reminder_bot']
reminders_collection = db['reminders']
reply_text_collection = db.get_collection('reply_text')

def get_random_text(type):
    """Fetch a random text from the 'reply_text' collection based on the type."""
    try:
        documents = list(reply_text_collection.find({'type': type}))
        if documents:
            return random.choice(documents)['text']
    except errors.PyMongoError as e:
        print(f"Database error: {e}")
    return None

def initialize_hive_client(api_index=0):
    """Initialize the Hive client with a specific API node."""
    hive = Hive(keys=[HIVE_POSTING_KEY], node=HIVE_API_NODES[api_index % len(HIVE_API_NODES)])
    return hive

def process_reminders():
    """Process the reminders and reply to comments when their time is up."""
    current_time = datetime.utcnow()
    remaining_reminders = []

    # Fetch reminders from MongoDB
    reminders = reminders_collection.find()

    for reminder in reminders:
        target_timestamp = reminder.get('target_timestamp')
        
        if isinstance(target_timestamp, str):
            try:
                target_timestamp = datetime.strptime(target_timestamp, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                # If the string cannot be parsed, delete the reminder
                print(f"Invalid target_timestamp format for reminder: {reminder['permlink']}. Deleting it.")
                reminders_collection.delete_one({'_id': reminder['_id']})
                continue
        
        elif not isinstance(target_timestamp, datetime):
            # If target_timestamp is neither a string nor a datetime, delete the reminder
            print(f"Invalid target_timestamp type for reminder: {reminder['permlink']}. Deleting it.")
            reminders_collection.delete_one({'_id': reminder['_id']})
            continue
        
        if current_time >= target_timestamp:
            print(f"Processing reminder: {reminder['author']}/{reminder['permlink']}")
            reply_comment(reminder)
        else:
            remaining_reminders.append(reminder)

def reply_comment(reminder, api_index=0, max_retries=3):
    """Reply to the comment indicating the reminder is due, with retry logic on failure."""
    attempts = 0
    while attempts < max_retries:
        try:
            # Initialize Hive client
            hive = initialize_hive_client(api_index)

            # Create the comment object using author and permlink
            authorperm = f"@{reminder['author']}/{reminder['permlink']}"
            print(authorperm)
            comment = Comment(authorperm, steem_instance=hive)

            # Fetch random reminder notification and footer
            remind_notification = get_random_text('remind_notification') or DEFAULT_REMIND_NOTIFICATION
            print(remind_notification)
            footer = get_random_text('footer') or DEFAULT_FOOTER

            # Format the reply body
            reply_body = f"{remind_notification}"           
            if footer:
                reply_body = f"{reply_body}\n\n----\n{footer}"
                
            try:
                formatted_reply = eval(f"f'''{reply_body}'''")
                reply_body = formatted_reply
            except Exception as e:
                print(f"Error formatting remind_notification: {e}")

            # Post the reply
            comment.reply(reply_body, author=HIVE_USER)
            print(f"Replied with comment: {reminder['permlink']}")

            # Remove the reminder from reminders
            reminders_collection.delete_one({'_id': reminder['_id']})

            # Wait for 3 seconds to avoid overloading the blockchain with transactions
            time.sleep(3)

            # Exit the loop after a successful reply
            break

        except ContentDoesNotExistsException:
            print(f"Failed to reply: The comment @{reminder['author']}/{reminder['permlink']} does not exist.")
            break  # No need to retry if the comment does not exist

        except Exception as e:
            attempts += 1
            print(f"An error occurred while trying to reply (Attempt {attempts}/{max_retries}): {e}")
            if attempts >= max_retries:
                print(f"Failed to reply after {max_retries} attempts.")
            else:
                time.sleep(2)  # Wait before retrying

        if attempts >= max_retries and api_index < len(HIVE_API_NODES) - 1:
            print("Falling back to next API node...")
            reply_comment(reminder, api_index + 1, max_retries)
        elif attempts >= max_retries:
            print("Failed to reply with all API nodes.")

def time_ago(past_time, current_time=None):
    """Return a human-readable 'x ago' string."""
    if isinstance(past_time, str):
        past_time = parser.parse(past_time)
        
    if current_time is None:
        current_time = datetime.utcnow()  # Use current UTC time by default
    elif isinstance(current_time, str):
        current_time = parser.parse(current_time)

    delta = current_time - past_time

    if delta < timedelta(minutes=1):
        return "just now"
    elif delta < timedelta(hours=1):
        minutes = int(delta.total_seconds() // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif delta < timedelta(days=1):
        hours = int(delta.total_seconds() // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif delta < timedelta(weeks=1):
        days = delta.days
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif delta < timedelta(weeks=4):
        weeks = delta.days // 7
        return f"{weeks} week{'s' if weeks != 1 else ''} ago"
    else:
        months = delta.days // 30
        years = delta.days // 365
        if years >= 1:
            return f"{years} year{'s' if years != 1 else ''} ago"
        return f"{months} month{'s' if months != 1 else ''} ago"

