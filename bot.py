import os
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext

import gspread
from google.oauth2.service_account import Credentials
import json

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration from environment variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SHEET_ID = os.environ.get("SHEET_ID")
GOOGLE_CREDS_JSON = os.environ.get("GOOGLE_CREDENTIALS")

# Connect to Google Sheets
sheet = None
if GOOGLE_CREDS_JSON and SHEET_ID:
    creds_info = json.loads(GOOGLE_CREDS_JSON)
    creds = Credentials.from_service_account_info(
        creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gs_client = gspread.authorize(creds)
    try:
        spreadsheet = gs_client.open_by_key(SHEET_ID)
        sheet = spreadsheet.worksheet("leads_usernames_(API)")
    except Exception as e:
        logger.error(f"Error opening sheet: {e}")
else:
    logger.warning("Google Sheets not configured properly!")

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    token = None
    if context.args:
        token = context.args[0]

    username = user.username or ""
    user_id = user.id
    now = datetime.utcnow().strftime("%d/%m/%Y %H:%M:%S")

    if sheet:
        try:
            if token:
                try:
                    cell = sheet.find(token)
                    row_number = cell.row
                    sheet.update_cell(row_number, 4, username)
                    sheet.update_cell(row_number, 5, str(user_id))
                    sheet.update_cell(row_number, 6, now)
                    logger.info(f"Updated existing token row: {token}")
                except gspread.exceptions.CellNotFound:
                    # Token not found, append new
                    sheet.append_row([token, "", "", username, str(user_id), now])
                    logger.info(f"Token not found, new row added: {token}")
            else:
                # No token passed
                sheet.append_row(["", "", "", username, str(user_id), now])
                logger.info(f"No token, added new user {username}")
        except Exception as e:
            logger.error(f"Error updating sheet: {e}")

    # Send welcome message
    welcome_text = f"✅ Thanks {user.first_name} for your interest!\n\nPlease choose:"
    buttons = [
        [InlineKeyboardButton("➡️ DM Us", url="https://t.me/m/mhWzJm62OGEy")],
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/+k-0NPJLoj-5kNTlk")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    context.bot.send_message(chat_id=chat_id, text=welcome_text, reply_markup=reply_markup)

def main() -> None:
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()
    logger.info("Bot started polling...")
    updater.idle()

if __name__ == "__main__":
    main()
