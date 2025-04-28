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

# Load configuration
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SHEET_ID = os.environ.get("SHEET_ID")

# Hardcoded Google credentials
GOOGLE_CREDS_JSON = """
{
  "type": "service_account",
  "project_id": "black-network-451123-f9",
  "private_key_id": "7add59e64e112b3f1f877c9ad4130cb34f4ddeb4",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCztiMpxU5jlpQ5\\nGECmmaAw0yKyrHx0AgTgUauzzdJvi5AV+e4xywny53oqE/36UIUhI9CEk3VVrEll\\n09SZxAY/4PlrUydiawjMwaAzgt8/JeaivFZhDDhrJjVTNB5e+eB7FX78U2XinlHD\\nh9mEToKWMHLAM/lLSKTmJ4xBVvRhXadPUC/9wkIjsYMRacSa942q6J3tRuSV+lSD\\n3MywTYp4mYc3V159SBzahb+Bk7WKXwCcokBd5V8R1DlwJ0zohIb+qY/b0LQqlm0R\\navnrsyKhr2L7w2GN3q6gfoI8lEX0qz1U4L+4OZ/Sl2ZETcg0TObOs5+PPZZGi7Z4\\nRLGBEOpFAgMBAAECggEAIr5aj3uOE2pb9yrVavAl/HKBUY5P1ETEqRKZEb6/yaFv\\nhpQmhRlmL8ApSePKFSAGkPjh2hPBGkJgAVACGQVBGQ33YpS1t00Oqzle7b6GRyje\\nbUVgpMwOR0bghdi8a2u/RsSJ46IC/1xQ3e7QcogULpGoybhyoKene7iXINW9EuqL\\niOnQL3uJ5i/l0OGiKGxNOqlnmohDka2oKV+G7+ObniCrs5wzqjoATQC1a6ott4D5\\nQL45o/+5uMzUZRJBv29EGPM+cKw6CywaPwHL58BhZfMLGGVOCJbrom5jrTqW3jyd\\noqnWJRtTYCLAoL/5+DqPoc/pXotPjf2aE2sCn4FbsQKBgQDfuZpK+F94X/2JY6vV\\nFhwT4d8hare9HrLFzwZ7SKWgpAKN66cZdlY6p57PbSMXY4y70UHlWHs/2l7Lx1eW\\nRJIkuORC3AQqmMjiH3l9t7WdGdWlZuDGikTCxkzjK0hV+FArL7tqhULo4BYGDVHV\\njbtW+UB/ssn9fzSJdg1hfcDWFQKBgQDNoxGoZo+7KCkP50QcI+FOiaL/RZGPwRVH\\n8D2VZAc6vaqm1Yr54b/e/w0i9UbsKKLNbNLIZTaa9eIJDn570LcgqHly9zqQOA4j\\noXEBKjh3Uzfb1FSOmbBF/S2QJNgun8rz2joaKB6QXfJpT9v22V97Y5rVViqvjGet\\nP4kyX0Z/cQKBgDgL5S1W34PmeDuM7qUpLsuEUEOs2m7UW/DWFkeYQXXm4ITxPiFQ\\n1fVHvK82Jg5b8Au1No7gBbBPYmQmgjiw4PO2Jejh+WE6eUi8ndDyztqWeEFBbpoO\\nVX998hEO7MYsuNi40niy/bodOSc2+wNGyGHXe2MCRTvuPBkbq+p6eG6pAoGBAITd\\n7WXaxtnNzCJLcnWgNU7Sna/E2pWA02hE8PWayRUKQb5EUeS9GYVTVMCWrLmgU/jZ\\nbKQwyYR8hQ0HAXCs3fZLBRXkakGPBou9H0/6YLuw2HHAktYEtaGzQYJWXBxcAP1o\\nrowCCiWLnjqvb9figdAu/ncDktcUqFSHrfUPHHTxAoGBAM1k7qMXvaKH42wd6MFE\\n2PonzgNAKJ4nVMRiyiEOHj2z6QLj5O+yPKYdMpjSa8pAfq0iU/fvCQNrcBbnHmTv\\nbpGJC3zVMysPWsfSOi5fZABu6MCQu3Kba6wpqkEBfwakvqUpbjuSSapuz5Gma6J3\\no0mABaJOvSpojKcF/9UXzIOn\\n-----END PRIVATE KEY-----\\n",
  "client_email": "telegrambotsheetsaccess@black-network-451123-f9.iam.gserviceaccount.com",
  "client_id": "106711742149730374889",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/telegrambotsheetsaccess%40black-network-451123-f9.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
"""

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
                    sheet.append_row([token, "", "", username, str(user_id), now])
                    logger.info(f"Token not found, new row added: {token}")
            else:
                sheet.append_row(["", "", "", username, str(user_id), now])
                logger.info(f"No token, added new user {username}")
        except Exception as e:
            logger.error(f"Error updating sheet: {e}")

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
