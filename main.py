import os
import time
import threading
from listener import listen_for_comments, get_latest_block_num, load_blacklist
from reply import handle_new_comment
from resumption import load_last_block, save_last_block
from reminder_handler import process_reminders

# Configuration
BLOCK_RANGE = 20
QUIT_TIMEOUT = 30  # 30 seconds timeout for quitting on error

def quit_if_timeout():
    """Wait for user input or timeout to quit the application."""
    print(f"No input received. The application will quit in {QUIT_TIMEOUT} seconds...")
    timeout_event = threading.Event()
    input_thread = threading.Thread(target=lambda: input("Press Enter to stop the application...") or timeout_event.set())
    input_thread.start()

    timeout_event.wait(QUIT_TIMEOUT)
    if not timeout_event.is_set():
        print("Timeout reached. Exiting the application.")
        os._exit(1)

def main():
    # Load the last processed block number or get the latest block number if not available
    latest_block_num = get_latest_block_num()

    last_block = load_last_block() or latest_block_num
    end_block = last_block + BLOCK_RANGE - 1
    
    if latest_block_num < end_block:
        end_block = latest_block_num
        if last_block > latest_block_num:
            last_block = latest_block_num

    # Start listening for comments
    while True:
        try:
            comments = listen_for_comments(last_block, end_block, load_blacklist())
            for comment in comments:
                handle_new_comment(comment)

            # Process reminders
            process_reminders()

            # Update the block range for the next iteration
            last_block = end_block + 1
            end_block = last_block + BLOCK_RANGE - 1
            
            latest_block_num = get_latest_block_num()
            if latest_block_num < end_block:
                end_block = latest_block_num
                if last_block > latest_block_num:
                    last_block = latest_block_num
                
            # Save last_block before exiting if reached the latest block
            save_last_block(end_block + 1)
            if last_block == latest_block_num:
                print("Last block is the same as the latest block. Exiting the application.")
                save_last_block(last_block)
                break  # Quit the loop to exit

        except Exception as e:
            print(f"An error occurred: {e}")
            quit_if_timeout()  # Wait for timeout or user input to quit

if __name__ == "__main__":
    main()

