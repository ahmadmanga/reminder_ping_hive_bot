import csv
from datetime import datetime

REMINDER_LIST_FILE = 'ReminderList.csv'
FINISHED_TASKS_FILE = 'FinishedTasks.csv'

def read_reminder_list():
    """Read the reminder list from the CSV file."""
    reminders = []
    try:
        with open(REMINDER_LIST_FILE, mode='r') as file:
            reader = csv.reader(file)
            for row in reader:
                reminders.append(row)
    except FileNotFoundError:
        # File doesn't exist yet, return empty list
        pass
    return reminders

def add_to_reminder_list(comment, target_timestamp):
    """Add a new reminder to the CSV file."""
    with open(REMINDER_LIST_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([comment['author'], comment['permlink'], comment['body'], target_timestamp.isoformat()])

def add_to_finished_tasks(reminder):
    """Add a completed reminder to the finished tasks CSV file."""
    with open(FINISHED_TASKS_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(reminder)

