import discord
from discord.ext import commands, tasks
from discord import ButtonStyle
from discord.ui import View, Select, Button
import requests
import datetime

# Discord Bot authentication token
# Replace this token with your own token (without extra quotes)
# Example format: YOUR_DISCORD_BOT_TOKEN_HERE
TOKEN = "YOUR_DISCORD_BOT_TOKEN_HERE"  # Replace with your actual token

# RapidAPI configuration
RAPIDAPI_KEY = "YOUR_RAPID_API_HERE"
RAPIDAPI_HOST = "gmailnator.p.rapidapi.com"
API_HEADERS = {
    "x-rapidapi-key": RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
    "Content-Type": "application/json"
}

# Configure bot permissions (intents)
intents = discord.Intents.default()
intents.message_content = True

# Initialize the bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Store generated emails for auto-refresh functionality
active_emails = {}  # {email: {'expiry_time': datetime, 'channel_id': channel_id, 'message_id': message_id, 'seen_message_ids': set()}}

# Store panel messages for updates
panel_messages = {}  # {channel_id: message}

# Main menu dropdown class
class MainMenuView(View):
    def __init__(self):
        super().__init__(timeout=None)  # No timeout for the main menu
        
        # Create dropdown menu
        options = [
            discord.SelectOption(label="Generate Email", description="Generates a temporary email", value="generate_email"),
            discord.SelectOption(label="Check Specific Email", description="Check the inbox of a specific email", value="check_email")
        ]
        
        # Add dropdown menu to the view
        self.add_item(MainMenuSelect(options))

# Main menu selector class
class MainMenuSelect(Select):
    def __init__(self, options):
        super().__init__(placeholder="Select an option...", min_values=1, max_values=1, options=options)
    
    async def callback(self, interaction):
        # Get the selected option
        selected_option = self.values[0]
        
        if selected_option == "generate_email":
            # Generate a single email
            await generate_email(interaction)
        
        elif selected_option == "check_email":
            # Show form to check specific email
            await show_check_email_form(interaction)

# Email panel view class
class EmailPanelView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
        # Add buttons
        self.add_item(Button(style=ButtonStyle.primary, label="Generate Another Email", custom_id="generate_another_email"))
        self.add_item(Button(style=ButtonStyle.secondary, label="Refresh", custom_id="refresh_email"))
        self.add_item(Button(style=ButtonStyle.danger, label="Back to Menu", custom_id="back_to_menu"))

# Email check form view class
class CheckEmailView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
        # Add buttons for form submission
        self.add_item(Button(style=ButtonStyle.primary, label="Check", custom_id="submit_check_email"))
        self.add_item(Button(style=ButtonStyle.secondary, label="Cancel", custom_id="cancel_check_email"))
    
    async def interaction_check(self, interaction):
        custom_id = interaction.data["custom_id"]
        
        if custom_id == "cancel_check_email":
            # Cancel and show main menu
            await show_main_menu(interaction.channel)
            await interaction.message.delete()
        
        return True

# Function to validate emails - rejects emails with '+', '=', or '#' and accepts only @gmail.com
def is_valid_email(email):
    """Checks if the email is valid (doesn't contain unwanted characters and ends with @gmail.com)"""
    if '+' in email or '=' in email or '#' in email:
        return False
    if not email.lower().endswith("@gmail.com"):
        return False
    return True

@bot.event
async def on_ready():
    print(f"{bot.user.name} successfully connected!")
    
    # Find a channel to send the initial message
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                # Send the initial panel
                await show_main_menu(channel)
                check_emails.start()  # Start auto-refresh task
                return  # Exit after successfully sending the message
            except Exception as e:
                print(f"Could not send message to {channel.name}: {e}")
                # Continue trying another channel

# Function to show the main menu
async def show_main_menu(channel):
    """Displays the main menu with available options"""
    embed = discord.Embed(
        title="📧 Temporary Email Generator",
        description="Welcome to the temporary email generator! Select an option below to begin.",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="Features",
        value="• Generation of temporary emails\n• Automatic inbox monitoring\n• Real-time notifications",
        inline=False
    )
    
    embed.set_footer(text="Emails are automatically monitored for 3 minutes")
    
    # Create options menu
    view = MainMenuView()
    
    # Send message with menu
    message = await channel.send(embed=embed, view=view)
    
    # Store panel message for future updates
    panel_messages[channel.id] = message

# Function to generate an email
async def generate_email(interaction):
    """Generates a temporary email and displays it in a new panel"""
    # Respond to the interaction to avoid timeout error
    await interaction.response.defer(ephemeral=True)
    
    # Update message with "generating email" status
    loading_embed = discord.Embed(
        title="📧 Generating Temporary Email",
        description="⏳ Please wait while we generate your email...",
        color=discord.Color.orange()
    )
    
    await interaction.message.edit(embed=loading_embed, view=None)
    
    # Generate the email
    url = "https://gmailnator.p.rapidapi.com/generate-email"
    payload = {"options": [3]}  # Use all available options for more variety
    
    try:
        # Try up to 5 times to get a valid email
        attempts = 0
        max_attempts = 5
        valid_email_found = False
        
        while attempts < max_attempts and not valid_email_found:
            response = requests.post(url, json=payload, headers=API_HEADERS)
            data = response.json()
            
            if "email" in data:
                email = data["email"]
                
                if is_valid_email(email):
                    # Valid email found
                    valid_email_found = True
                    
                    # Add to active emails for auto-refresh
                    expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=3)
                    active_emails[email] = {
                        'expiry_time': expiry_time,
                        'channel_id': interaction.channel.id,
                        'message_id': interaction.message.id,
                        'seen_message_ids': set()
                    }
                    
                    # Create email panel
                    await show_email_panel(interaction, email)
                else:
                    # Email contains invalid characters, try again
                    print(f"Email rejected (contains invalid characters): {email}")
                    attempts += 1
            else:
                attempts += 1
        
        # If no valid email found after several attempts
        if not valid_email_found:
            error_embed = discord.Embed(
                title="❌ Error",
                description="Could not generate a valid email after several attempts. Please try again.",
                color=discord.Color.red()
            )
            
            # Add button to return to main menu
            view = View()
            view.add_item(Button(style=ButtonStyle.primary, label="Back to Menu", custom_id="back_to_menu"))
            
            await interaction.message.edit(embed=error_embed, view=view)
    
    except Exception as e:
        # In case of error, show error message
        error_embed = discord.Embed(
            title="❌ Error",
            description=f"An error occurred while generating the email: {str(e)}",
            color=discord.Color.red()
        )
        
        # Add button to return to main menu
        view = View()
        view.add_item(Button(style=ButtonStyle.primary, label="Back to Menu", custom_id="back_to_menu"))
        
        await interaction.message.edit(embed=error_embed, view=view)

# Function to show email panel
async def show_email_panel(interaction, email):
    """Displays a panel with generated email information"""
    embed = discord.Embed(
        title="📧 Temporary Email Generated",
        description=f"**Email:** {email}\n\nThis inbox will be automatically monitored for 3 minutes.",
        color=discord.Color.green()
    )
    
    embed.add_field(
        name="📥 Inbox",
        value="No messages received yet. Messages will appear here automatically.",
        inline=False
    )
    
    # Create view with buttons
    view = EmailPanelView()
    
    # Update message with email panel
    await interaction.message.edit(embed=embed, view=view)
    
    # Update message ID in active emails registry
    active_emails[email]['message_id'] = interaction.message.id
    print(f"Auto-refresh enabled for {email} with message_id {interaction.message.id}")

# Function to show email check form
async def show_check_email_form(interaction):
    """Displays a form to check a specific email"""
    embed = discord.Embed(
        title="📧 Check Specific Email",
        description="To check the inbox of a specific email, type the email address in the chat below.",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="Instructions",
        value="1. Type the complete email address\n2. Click Check\n3. The result will be displayed here",
        inline=False
    )
    
    # Create view with buttons
    view = CheckEmailView()
    
    # Update message with form
    await interaction.response.edit_message(embed=embed, view=view)

@bot.event
async def on_interaction(interaction):
    """Handles interactions with UI components"""
    if not interaction.data:
        return
    
    # Check if it's a button interaction
    if interaction.data.get("component_type") == 2:  # 2 = Button
        custom_id = interaction.data.get("custom_id")
        
        if custom_id == "back_to_menu":
            # Disable auto-refresh for the email associated with this message
            message_id = interaction.message.id
            emails_to_remove = []
            
            for email, data in active_emails.items():
                if data.get('message_id') == message_id:
                    emails_to_remove.append(email)
            
            # Remove emails from monitoring
            for email in emails_to_remove:
                del active_emails[email]
                print(f"Auto-refresh disabled for {email} when returning to menu")
            
            # Return to main menu
            await interaction.message.delete()
            await show_main_menu(interaction.channel)
            await interaction.response.defer()
        
        elif custom_id == "generate_another_email":
            # Disable auto-refresh for current email before generating a new one
            message_id = interaction.message.id
            emails_to_remove = []
            
            for email, data in active_emails.items():
                if data.get('message_id') == message_id:
                    emails_to_remove.append(email)
            
            # Remove emails from monitoring
            for email in emails_to_remove:
                del active_emails[email]
                print(f"Auto-refresh disabled for {email} before generating new email")
            
            # Generate another email
            await generate_email(interaction)
            await interaction.response.defer()
        
        elif custom_id == "refresh_email":
            # Manually refresh inbox
            # Don't use defer here as it will be used in check_specific_email
            
            # Find email associated with this message
            for email, data in active_emails.items():
                if data.get('message_id') == interaction.message.id:
                    # Check inbox
                    await check_specific_email(interaction, email)
                    break
        
        elif custom_id == "submit_check_email":
            # Extract email from message content
            embed = interaction.message.embeds[0]
            email_content = embed.fields[0].value if embed.fields else None
            
            if email_content and "@" in email_content:
                # Extract email address
                email = email_content.split("\n")[0].strip()
                
                # Check inbox
                await check_specific_email(interaction, email)
            else:
                # Invalid or missing email
                await interaction.response.send_message(
                    "⚠️ Invalid or missing email. Please try again.",
                    ephemeral=True
                )

# Function to check a specific email
async def check_specific_email(interaction, email):
    """Checks the inbox of a specific email"""
    # Respond to interaction to avoid timeout error
    try:
        # Try to respond to the interaction, but it may have already been responded to
        await interaction.response.defer(ephemeral=True)
    except discord.errors.InteractionResponded:
        # Interaction was already responded to, we can continue
        pass
    
    # Update message with "checking" status
    loading_embed = discord.Embed(
        title="📧 Checking Email",
        description=f"⏳ Checking inbox for {email}...",
        color=discord.Color.orange()
    )
    
    await interaction.message.edit(embed=loading_embed, view=None)
    
    try:
        # Check inbox
        inbox = await check_inbox(email)
        
        if inbox:
            if len(inbox) > 0:
                # Create embed with messages
                embed = discord.Embed(
                    title=f"📬 Inbox for {email}",
                    description=f"Found {len(inbox)} messages",
                    color=discord.Color.green()
                )
                
                for msg in inbox:
                    embed.add_field(
                        name=f"📩 From: {msg.get('from', 'Unknown')} | Subject: {msg.get('subject', 'No Subject')}",
                        value=f"Received: {msg.get('date', 'Unknown Date')}",
                        inline=False
                    )
            else:
                # No messages found
                embed = discord.Embed(
                    title=f"📭 Inbox for {email}",
                    description="No messages found",
                    color=discord.Color.blue()
                )
        else:
            # Error checking inbox
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to check inbox. Please try again.",
                color=discord.Color.red()
            )
        
        # Add buttons
        view = EmailPanelView()
        
        # Update message with result
        await interaction.message.edit(embed=embed, view=view)
    
    except Exception as e:
        # In case of error, show error message
        error_embed = discord.Embed(
            title="❌ Error",
            description=f"An error occurred while checking the inbox: {str(e)}",
            color=discord.Color.red()
        )
        
        # Add button to return to main menu
        view = View()
        view.add_item(Button(style=ButtonStyle.primary, label="Back to Menu", custom_id="back_to_menu"))
        
        await interaction.message.edit(embed=error_embed, view=view)

async def check_inbox(email):
    """Check inbox for a specific email"""
    url = "https://gmailnator.p.rapidapi.com/inbox"
    
    payload = {
        "email": email,
        "limit": 3  # Limited to 3 most recent messages
    }
    
    try:
        response = requests.post(url, json=payload, headers=API_HEADERS)
        return response.json()
    except Exception as e:
        print(f"Error checking inbox: {e}")
        return None

@tasks.loop(seconds=30)
async def check_emails():
    """Periodically check inboxes of all active emails"""
    current_time = datetime.datetime.now()
    emails_to_remove = []
    
    for email, data in active_emails.items():
        if current_time > data['expiry_time']:
            emails_to_remove.append(email)
            print(f"Email expired: {email}")
            continue
        
        try:
            channel_id = data['channel_id']
            message_id = data.get('message_id')
            
            channel = bot.get_channel(channel_id)
            if not channel:
                continue
            
            # Try to get message by ID, if available
            message = None
            if message_id:
                try:
                    message = await channel.fetch_message(message_id)
                except:
                    # Message not found, may have been deleted
                    pass
            
            inbox = await check_inbox(email)
            
            if inbox and len(inbox) > 0:
                # Track new messages
                new_messages = []
                
                # If we don't have a seen_message_ids set for this email, create one
                if 'seen_message_ids' not in active_emails[email]:
                    active_emails[email]['seen_message_ids'] = set()
                
                # Check for new messages
                for msg in inbox:
                    # Use message ID or a combination of from+subject+date as unique identifier
                    msg_id = msg.get('id', f"{msg.get('from', '')}-{msg.get('subject', '')}-{msg.get('date', '')}")
                    
                    if msg_id not in active_emails[email]['seen_message_ids']:
                        new_messages.append(msg)
                        active_emails[email]['seen_message_ids'].add(msg_id)
                
                # Only send notification if there are new messages
                if new_messages and message:
                    # Update existing panel with new messages
                    embed = message.embeds[0]
                    
                    # Update inbox field
                    inbox_content = ""
                    for msg in inbox:
                        inbox_content += f"📩 **From:** {msg.get('from', 'Unknown')}\n"
                        inbox_content += f"📑 **Subject:** {msg.get('subject', 'No Subject')}\n"
                        inbox_content += f"🕒 **Received:** {msg.get('date', 'Unknown Date')}\n\n"
                    
                    # Replace inbox field, or add if it doesn't exist
                    found = False
                    for i, field in enumerate(embed.fields):
                        if field.name == "📥 Inbox" or "Inbox" in field.name:
                            embed.set_field_at(
                                i,
                                name="📥 Inbox (Updated)",
                                value=inbox_content if inbox_content else "No messages received yet.",
                                inline=False
                            )
                            found = True
                            break
                    
                    if not found:
                        embed.add_field(
                            name="📥 Inbox",
                            value=inbox_content if inbox_content else "No messages received yet.",
                            inline=False
                        )
                    
                    # Update message
                    await message.edit(embed=embed)
                
                elif new_messages and channel:
                    # If we don't have the original message, send a new notification
                    embed = discord.Embed(
                        title=f"📬 New Messages for {email}",
                        color=discord.Color.green()
                    )
                    
                    for msg in new_messages:
                        embed.add_field(
                            name=f"📩 From: {msg.get('from', 'Unknown')} | Subject: {msg.get('subject', 'No Subject')}",
                            value=f"Received: {msg.get('date', 'Unknown Date')}",
                            inline=False
                        )
                    
                    # Add buttons
                    view = EmailPanelView()
                    
                    new_message = await channel.send(embed=embed, view=view)
                    active_emails[email]['message_id'] = new_message.id
        
        except Exception as e:
            print(f"Error checking inbox for {email}: {e}")
    
    # Remove expired emails
    for email in emails_to_remove:
        del active_emails[email]

# Run the bot
if __name__ == "__main__":
    print("Starting Discord bot...")
    bot.run(TOKEN)