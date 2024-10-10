import os
import time
from datetime import datetime, timedelta
from dateutil import parser
from dotenv import load_dotenv
from beem import Hive
from beem.comment import Comment
from beem.exceptions import ContentDoesNotExistsException
from pymongo import MongoClient
from reminder_handler import get_random_text, time_ago
import re

# Load environment variables
load_dotenv()
HIVE_USER = os.getenv('HIVE_USERNAME')
HIVE_POSTING_KEY = os.getenv('POSTING_KEY')
MONGO_URI = os.getenv('MONGO_URI')

# List of Hive API nodes
HIVE_API_NODES = [
    'https://api.hive.blog',
    'https://api.deathwing.me',
    'https://api.openhive.network'
]

# MongoDB client
client = MongoClient(MONGO_URI)
db = client['reminder_bot']
upcoming_reminders = db['reminders']
users_collection = db['list_of_users']

def initialize_hive_client(api_index=0):
    """Initialize the Hive client with a specific API node."""
    hive = Hive(keys=[HIVE_POSTING_KEY], node=HIVE_API_NODES[api_index % len(HIVE_API_NODES)])
    return hive

def handle_new_comment(comment):
    """Handle new comments, check for !RemindMe and reply if necessary."""
    if "!remindme" in comment['body'].lower():
        time_string = extract_time_string(comment['body'])
        if time_string:
            block_timestamp = comment['block_timestamp']
            target_timestamp = calculate_target_timestamp(block_timestamp, time_string)
            if target_timestamp:
                add_to_reminder_list(comment, target_timestamp)
                reply_body = get_random_text("confirm_listing")
                
                try:
                    formatted_reply = eval(f"f'''{reply_body}'''")
                    reply_body = formatted_reply
                except Exception as e:
                    print(f"Error formatting remind_notification: {e}")
                
                reply_to_comment(initialize_hive_client(), comment, reply_body)
            else:
                reply_with_error(comment)
        else:
            print(f"No valid time found in comment: {comment['author']}/{comment['permlink']}")
            reply_with_error(comment)
    else:
        pass

def extract_time_string(body):
    """Extract everything on the same line as '!remindme' as the time string."""
    match = re.search(r'!remindme\s*(.*)', body, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def calculate_target_timestamp(block_timestamp, time_string):
    """Calculate the target timestamp based on the provided time string."""
    time_string = time_string.lower().strip()
        
    # Stage 1: Manual parsing for "in {number} {unit}" pattern
match = re.match(
        r'(?:in\s+)?(\d+(?:\.\d+)?|\d+:\d+)\s*(second[s]?|sec[s]?|minute[s]?|min[s]?|hour[s]?|hr[s]?|day[s]?|week[s]?|month[s]?|moon[s]?|year[s]?)(?:\s+and\s+(\d+(?:\.\d+)?|\d+:\d+)\s*(second[s]?|sec[s]?|minute[s]?|min[s]?|hour[s]?|hr[s]?|day[s]?|week[s]?|month[s]?|moon[s]?|year[s]?))?',
        time_string
    )
    
    if match:
        # First amount and unit
        amount1, unit1 = match.group(1), match.group(2)
        # Parse the first amount, handling fractional and time format (1:30 hours)
        if ':' in amount1:
            hours, minutes = map(float, amount1.split(':'))
            amount1 = hours + minutes / 60
        else:
            amount1 = float(amount1)
        
        # Second amount and unit (if present)
        amount2 = float(match.group(4)) if match.group(3) else 0
        unit2 = match.group(4) if match.group(4) else None
        
        # Parse the second amount if provided
        if unit2:
            if ':' in amount2:
                hours, minutes = map(float, amount2.split(':'))
                amount2 = hours + minutes / 60
            else:
                amount2 = float(amount2)

        # Time delta calculation based on units
        delta = timedelta()
        
        # Calculate delta for the first unit
        if 'second' in unit1 or 'sec' in unit1:
            delta += timedelta(seconds=amount1)
        elif 'minute' in unit1 or 'min' in unit1:
            delta += timedelta(minutes=amount1)
        elif 'hour' in unit1 or 'hr' in unit1:
            delta += timedelta(hours=amount1)
        elif 'day' in unit1:
            delta += timedelta(days=amount1)
        elif 'week' in unit1:
            delta += timedelta(weeks=amount1)
        elif 'month' in unit1 or 'moon' in unit1:
            delta += timedelta(days=amount1 * 30)  # Approximate 1 month as 30 days
        elif 'year' in unit1:
            delta += timedelta(days=amount1 * 365)  # Approximate 1 year as 365 days
        
        # Repeat for the second unit if present
        if unit2:
            if 'second' in unit2 or 'sec' in unit2:
                delta += timedelta(seconds=amount2)
            elif 'minute' in unit2 or 'min' in unit2:
                delta += timedelta(minutes=amount2)
            elif 'hour' in unit2 or 'hr' in unit2:
                delta += timedelta(hours=amount2)
            elif 'day' in unit2:
                delta += timedelta(days=amount2)
            elif 'week' in unit2:
                delta += timedelta(weeks=amount2)
            elif 'month' in unit2 or 'moon' in unit2:
                delta += timedelta(days=amount2 * 30)
            elif 'year' in unit2:
                delta += timedelta(days=amount2 * 365)
        
        # Convert block timestamp to datetime
        block_timestamp = datetime.strptime(block_timestamp, '%Y-%m-%dT%H:%M:%S')
        target_timestamp = block_timestamp + delta
        return target_timestamp
    
    # Stage 2: Parsing with dateutil.parser
    elif re.search(r'\b(?:on|at)\s+(?:the\s+)?(?:(\w+),?\s+(\d{1,2})(?:st|nd|rd|th)?,?|(\d{1,2})(?:st|nd|rd|th)?,?(?:\s+(?:of\s+)?(\w+),?))?\s*(\d{4})?', time_string):
       try:
          specific_date = parser.parse(time_string, fuzzy=True)
          block_timestamp = datetime.strptime(block_timestamp, '%Y-%m-%dT%H:%M:%S')
          if specific_date.year == block_timestamp.year and specific_date.month < block_timestamp.month:
             specific_date = specific_date.replace(year=specific_date.year + 1)
          #if specific_date.hour == 0 and specific_date.minute == 0 and specific_date.second == 0:
          #   specific_date = specific_date.replace(hour=block_timestamp.hour, minute=block_timestamp.minute, second=block_timestamp.second)
             
          return specific_date
    except (ValueError, OverflowError):
        pass
            
    # Stage 3: Return None if unable to parse
    return None

def add_to_reminder_list(comment, target_timestamp):
    """Add the comment and target timestamp to the reminder list (MongoDB)."""
    reminder_data = {
        'author': comment['author'],
        'permlink': comment['permlink'],
        'parent_author': comment['parent_author'],
        'parent_permlink': comment['parent_permlink'],
        'body': comment['body'],
        'block_timestamp': comment['block_timestamp'],
        'target_timestamp': target_timestamp
    }
    upcoming_reminders.insert_one(reminder_data)
    print(f"Added reminder for {comment['author']} at {target_timestamp}")

def reply_to_comment(hive, comment, reply_body, increase_count=True):
    """Reply to the comment and optionally update user's remindme count."""
    try:
        if increase_count:
            user = users_collection.find_one({'author': comment['author']})
            if user:
                users_collection.update_one({'author': comment['author']}, {'$inc': {'remindme_count': 1}})
                print(f"Updated remindme_count for {comment['author']}")
            else:
                new_user = {'author': comment['author'], 'remindme_count': 1, 'premium': 0}
                users_collection.insert_one(new_user)
                print(f"Added new user: {comment['author']}")

        # Reply to the comment on Hive        
        comment_obj = Comment(f"@{comment['author']}/{comment['permlink']}", steem_instance=hive)
        reply = comment_obj.reply(body=reply_body, author=HIVE_USER)
        print(f"Replied with comment: {comment['permlink']}")
        time.sleep(3)
        
    except ContentDoesNotExistsException:
        print(f"Failed to reply: The comment @{comment['author']}/{comment['permlink']} does not exist.")
    except Exception as e:
        print(f"An error occurred while replying: {e}")

def reply_with_error(comment, api_index=0):
    """Reply with an error message if time parsing fails, with fallback API nodes."""
    hive = initialize_hive_client(api_index)
    reply_body = get_random_text("parsing_error")
    
    try:
        reply_to_comment(hive, comment, reply_body, increase_count=False)
    except Exception as e:
        print(f"Error replying with {HIVE_API_NODES[api_index % len(HIVE_API_NODES)]}: {e}")
        if api_index < len(HIVE_API_NODES) - 1:
            print("Falling back to next API node...")
            reply_with_error(comment, api_index + 1)
        else:
            print("Failed to reply with all API nodes.")

