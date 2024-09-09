# Reminder Ping Hive Bot

This bot is designed to interact with the Hive blockchain, MongoDB, and handle scheduled reminders for users. It listens to comments on Hive and replies to them when the reminder time is reached, all while being deployed and run via GitHub Actions.

## Features
- **Scheduled Reminders**: The bot processes reminders and replies to users when their reminders are due.
- **MongoDB Integration**: Stores and retrieves reminder templates and user data from MongoDB.
- **Hive Blockchain Interaction**: The bot listens to comments on the Hive blockchain and responds when necessary.
- **Automatic Deployment**: Deployed and triggered to run every 10 minutes using GitHub Actions.

## Installation
### Prerequisites
1. **Python 3.10+** - Ensure Python is installed.
2. **MongoDB** - The bot interacts with a MongoDB database to store and manage reminders.
3. **Hive Account** - You will need a Hive account to interact with the blockchain.

### Setting up the Bot
1. Clone this repository:
   ```bash
   git clone https://github.com/ahmadmanga/reminder_ping_hive_bot.git
   cd reminder_ping_hive_bot
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables by creating a `.env` file:
   ```
   HIVE_USER=<your-hive-username>
   HIVE_POSTING_KEY=<your-posting-key>
   MONGO_URI=<your-mongodb-uri>
   ```

### Running the Bot Locally
You can run the bot locally by executing the main script:
```bash
python main.py
```

## Deployment
This bot is automatically deployed via **GitHub Actions**. The GitHub Action is scheduled to run every 10 minutes. 

Ensure you have the following secrets set up in your GitHub repository:
- `HIVE_USER`
- `HIVE_POSTING_KEY`
- `MONGO_URI`

## Usage
Once deployed, the bot will:
- Fetch and process reminders from MongoDB.
- Listen for new comments on the Hive blockchain.
- Respond to users based on their reminder requests.

## License
This project currently does not have a license. Feel free to reach out if you'd like to discuss licensing terms.

## Contributing
If you'd like to contribute to the project, please open an issue or submit a pull request!
