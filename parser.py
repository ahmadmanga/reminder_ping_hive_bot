import re
from datetime import datetime, timedelta

def parse_time_from_comment(comment):
    """Parse time information from a comment."""
    # Example patterns: "in 3 hours", "in 2 days", "tomorrow"
    time_patterns = [
        (r'in (\d+) (minute|hour|day|week)s?', lambda m: int(m.group(1))),
        (r'tomorrow', lambda m: 1)  # special case for "tomorrow"
    ]

    for pattern, get_value in time_patterns:
        match = re.search(pattern, comment)
        if match:
            time_unit = match.group(2) if len(match.groups()) > 1 else 'day'
            return timedelta(**{f'{time_unit}s': get_value(match)}), True

    # If no patterns matched, return None and a False flag
    return None, False

def calculate_target_timestamp(comment_timestamp, time_delta):
    """Calculate the target timestamp based on the parsed time delta."""
    return comment_timestamp + time_delta

# Example usage
if __name__ == "__main__":
    comment = "Remind me in 3 hours"
    time_delta, success = parse_time_from_comment(comment)
    if success:
        target_timestamp = calculate_target_timestamp(datetime.now(), time_delta)
        print(f"Target Timestamp: {target_timestamp}")
    else:
        print("Could not parse the time from the comment.")

