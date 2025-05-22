# Discord Temporary Email Generator

A Discord bot that generates temporary Gmail addresses, checks inboxes, and automatically monitors emails for new messages in real-time.

## 📧 Features

- **Generate temporary Gmail addresses** with a simple Discord interface
- **Real-time inbox monitoring** for 3 minutes after generation
- **Automatic notifications** when new emails arrive
- **User-friendly interface** with buttons and dropdown menus
- **Check specific email inboxes** on demand

## 🔧 Prerequisites

- Python 3.8 or higher
- A Discord account and a Discord bot token
- A RapidAPI key (for the GMail Nator API)

## 🚀 Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd discord-email-generator
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the bot:
   - Open `bot3.py` 
   - Replace the Discord bot token with your own token
   - Optionally, replace the RapidAPI key if you want to use your own

## 🔐 Setting Up Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Navigate to the "Bot" tab and click "Add Bot"
4. Under "Privileged Gateway Intents", enable "Message Content Intent"
5. Copy the bot token and add it to your `bot.py` file
6. Use the OAuth2 URL Generator in the "OAuth2" tab to generate an invite link:
   - Select the scopes: `bot`
   - Select the permissions: `Send Messages`, `Read Messages/View Channels`, `Embed Links`, `Attach Files`
7. Use the generated URL to invite the bot to your Discord server

## 📝 Usage

1. Run the bot:
   ```bash
   python bot.py
   ```

2. The bot will automatically post the main menu in the first available text channel:

   [Main Menu](https://imgur.com/dzaLDBo)

3. Use the dropdown menu to:
   - **Generate Email**: Creates a temporary Gmail address and displays it in a panel
   - **Check Specific Email**: Allows you to check the inbox of a specific email address

4. When an email is generated, you'll see a panel with:
   - The email address
   - Buttons for generating another email, refreshing the inbox, or returning to the main menu
   - An inbox area that will automatically update with new messages

## ⚙️ Auto-Refresh Feature

- All generated emails are automatically monitored for **3 minutes** after generation
- If new messages arrive during this time, the bot will automatically update the email panel
- You can also manually refresh the inbox using the "Refresh" button

## 🔍 Email Validation

The bot validates generated emails to ensure they:
- End with `@gmail.com`
- Don't contain special characters like `+`, `=`, or `#` that might cause issues

## 🔄 API Integration

This bot uses the GMail Nator API through RapidAPI:
- [GMail Nator API on RapidAPI](https://rapidapi.com/johndevz/api/gmailnator)

The API provides:
- Email generation
- Inbox checking
- Message retrieval

## 📋 Buttons and Controls

| Button | Description |
|--------|-------------|
| Generate Another Email | Creates a new temporary email address |
| Refresh | Manually checks the inbox for new messages |
| Back to Menu | Returns to the main menu |

## 🤔 Troubleshooting

- **API Rate Limits**: If you encounter errors when generating emails, you may have hit the RapidAPI rate limits. Consider upgrading your plan or waiting before making more requests.
- **Bot Permissions**: Ensure the bot has proper permissions to send messages and embeds in your Discord server.
- **Invalid Emails**: The bot automatically filters out invalid email formats. If it repeatedly fails to generate a valid email, try again later.

## 📄 License

This project is open-source and available under the MIT License.

## 🙏 Acknowledgements

- [discord.py](https://github.com/Rapptz/discord.py) for the Discord API wrapper
- [RapidAPI](https://rapidapi.com/) for hosting the GMail Nator API
- [GMail Nator](https://www.gmailnator.com/) for the temporary email service
