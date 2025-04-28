import logging
from datetime import datetime
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

import gspread
from google.oauth2.service_account import Credentials

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HARDCODED configuration
BOT_TOKEN = "7825910857:AAFohCr9B06mIDQGxfZMI_m_Yf2UbWI3lTc"
SHEET_ID = "14Lgu4JV5Nn2-r6kh8R3MHk11ai7sUul5akfNpv0xFtc"

# HARDCODED Google credentials
GOOGLE_CREDS_JSON = """
{ your service account JSON here }
"""  # Keep your full JSON here, same as before

# Connect to Google Sheets
sheet = None
try:
    creds_info = json.loads(GOOGLE_CREDS_JSON)
    creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")  # 🔥 FIX for Heroku
    creds = Credentials.from_service_account_info(
        creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gs_client = gspread.authorize(creds)
    spreadsheet = gs_client.open_by_key(SHEET_ID)
    sheet = spreadsheet.worksheet("leads_usernames_(API)")
except Exception as e:
    logger.error(f"Error opening sheet: {e}")

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    token = None
    if context.args:
        token = context.args[0]

    username = user.username or ""
    user_id = user.id
    now = datetime.utcnow().strftime("%d/%m/%Y %H:%M:%S")

    context.user_data['token'] = token  # Save token to user_data

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
                    sheet.append_row([token, "", "", username, str(user_id), now])
                    logger.info(f"Token not found, added new row: {token}")
            else:
                sheet.append_row(["", "", "", username, str(user_id), now])
                logger.info(f"No token, added new user {username}")
        except Exception as e:
            logger.error(f"Error updating sheet: {e}")

    # 🖌 Welcome message
    welcome_text = f"""🎉 Welcome {user.first_name}!

🚀 Thanks for your interest in TipsterGuruGoat!

👉 Please take the next step:

🔹 DM us directly  
🔹 Join our VIP Channel

Let's win together! 💸
"""
    buttons = [
        [InlineKeyboardButton("➡️ DM Us", callback_data='dm_us')],
        [InlineKeyboardButton("📢 Join Channel", callback_data='join_channel')]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    context.bot.send_message(chat_id=chat_id, text=welcome_text, reply_markup=reply_markup)

def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()

    user = query.from_user
    username = user.username or ""
    user_id = user.id
    now = datetime.utcnow().strftime("%d/%m/%Y %H:%M:%S")
    clicked_button = query.data

    # Find token (saved previously)
    token = context.user_data.get('token', '')

    if sheet:
        try:
            # Log button click in the sheet
            sheet.append_row([token, clicked_button, username, str(user_id), now])
            logger.info(f"Logged button click: {clicked_button} by {username}")
        except Exception as e:
            logger.error(f"Error logging button click: {e}")

    # Redirect to appropriate link
    if clicked_button == "dm_us":
        query.edit_message_text(text="Opening DM...")
        context.bot.send_message(chat_id=user.id, text="➡️ DM Us: https://t.me/m/SDmyGAMvNjY8")
    elif clicked_button == "join_channel":
        query.edit_message_text(text="Joining Channel...")
        context.bot.send_message(chat_id=user.id, text="📢 Join our Channel: https://t.me/+A6f68ahZ-PhkOGQ0")

def main() -> None:
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_click))

    updater.start_polling()
    logger.info("Bot started polling...")
    updater.idle()

if __name__ == "__main__":
    main()
