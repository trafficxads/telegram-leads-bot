import logging
from datetime import datetime
import json

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext

import gspread
from google.oauth2.service_account import Credentials

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HARDCODED configuration
BOT_TOKEN = "7825910857:AAFohCr9B06mIDQGxfZMI_m_Yf2UbWI3lTc"
SHEET_ID = "14Lgu4JV5Nn2-r6kh8R3MHk11ai7sUul5akfNpv0xFtc"

# HARDCODED Google credentials (copied from the JSON you uploaded)
GOOGLE_CREDS_JSON = {
  "type": "service_account",
  "project_id": "black-network-451123-f9",
  "private_key_id": "7add59e64e112b3f1f877c9ad4130cb34f4ddeb4",
  "private_key": """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCztiMpxU5jlpQ5
GECmmaAw0yKyrHx0AgTgUauzzdJvi5AV+e4xywny53oqE/36UIUhI9CEk3VVrEll
09SZxAY/4PlrUydiawjMwaAzgt8/JeaivFZhDDhrJjVTNB5e+eB7FX78U2XinlHD
h9mEToKWMHLAM/lLSKTmJ4xBVvRhXadPUC/9wkIjsYMRacSa942q6J3tRuSV+lSD
3MywTYp4mYc3V159SBzahb+Bk7WKXwCcokBd5V8R1DlwJ0zohIb+qY/b0LQqlm0R
avnrsyKhr2L7w2GN3q6gfoI8lEX0qz1U4L+4OZ/Sl2ZETcg0TObOs5+PPZZGi7Z4
RLGBEOpFAgMBAAECggEAIr5aj3uOE2pb9yrVavAl/HKBUY5P1ETEqRKZEb6/yaFv
hpQmhRlmL8ApSePKFSAGkPjh2hPBGkJgAVACGQVBGQ33YpS1t00Oqzle7b6GRyje
bUVgpMwOR0bghdi8a2u/RsSJ46IC/1xQ3e7QcogULpGoybhyoKene7iXINW9EuqL
iOnQL3uJ5i/l0OGiKGxNOqlnmohDka2oKV+G7+ObniCrs5wzqjoATQC1a6ott4D5
QL45o/+5uMzUZRJBv29EGPM+cKw6CywaPwHL58BhZfMLGGVOCJbrom5jrTqW3jyd
oqnWJRtTYCLAoL/5+DqPoc/pXotPjf2aE2sCn4FbsQKBgQDfuZpK+F94X/2JY6vV
FhwT4d8hare9HrLFzwZ7SKWgpAKN66cZdlY6p57PbSMXY4y70UHlWHs/2l7Lx1eW
RJIkuORC3AQqmMjiH3l9t7WdGdWlZuDGikTCxkzjK0hV+FArL7tqhULo4BYGDVHV
jbtW+UB/ssn9fzSJdg1hfcDWFQKBgQDNoxGoZo+7KCkP50QcI+FOiaL/RZGPwRVH
8D2VZAc6vaqm1Yr54b/e/w0i9UbsKKLNbNLIZTaa9eIJDn570LcgqHly9zqQOA4j
oXEBKjh3Uzfb1FSOmbBF/S2QJNgun8rz2joaKB6QXfJpT9v22V97Y5rVViqvjGet
P4kyX0Z/cQKBgDgL5S1W34PmeDuM7qUpLsuEUEOs2m7UW/DWFkeYQXXm4ITxPiFQ
1fVHvK82Jg5b8Au1No7gBbBPYmQmgjiw4PO2Jejh+WE6eUi8ndDyztqWeEFBbpoO
VX998hEO7MYsuNi40niy/bodOSc2+wNGyGHXe2MCRTvuPBkbq+p6eG6pAoGBAITd
7WXaxtnNzCJLcnWgNU7Sna/E2pWA02hE8PWayRUKQb5EUeS9GYVTVMCWrLmgU/jZ
bKQwyYR8hQ0HAXCs3fZLBRXkakGPBou9H0/6YLuw2HHAktYEtaGzQYJWXBxcAP1o
rowCCiWLnjqvb9figdAu/ncDktcUqFSHrfUPHHTxAoGBAM1k7qMXvaKH42wd6MFE
2PonzgNAKJ4nVMRiyiEOHj2z6QLj5O+yPKYdMpjSa8pAfq0iU/fvCQNrcBbnHmTv
bpGJC3zVMysPWsfSOi5fZABu6MCQu3Kba6wpqkEBfwakvqUpbjuSSapuz5Gma6J3
o0mABaJOvSpojKcF/9UXzIOn
-----END PRIVATE KEY-----""",
  "client_email": "telegrambotsheetsaccess@black-network-451123-f9.iam.gserviceaccount.com",
  "client_id": "106711742149730374889",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/telegrambotsheetsaccess%40black-network-451123-f9.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# Connect to Google Sheets
sheet = None
try:
    creds = Credentials.from_service_account_info(
        GOOGLE_CREDS_JSON, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    gs_client = gspread.authorize(creds)
    spreadsheet = gs_client.open_by_key(SHEET_ID)
    sheet = spreadsheet.worksheet("leads_usernames_(API)")
except Exception as e:
    logger.error(f"Error opening sheet: {e}")

def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id

    token = context.args[0] if context.args else None
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
                    logger.info(f"Token not found, added new row: {token}")
            else:
                sheet.append_row(["", "", "", username, str(user_id), now])
                logger.info(f"No token, added new user {username}")
        except Exception as e:
            logger.error(f"Error updating sheet: {e}")

    welcome_text = f"""🎉 Welcome {user.first_name}!

🚀 Thanks for your interest in TipsterGuruGoat!

👉 Please take the next step:

🔹 DM us directly  
🔹 Join our VIP Channel

Let's win together! 💸
"""
    buttons = [
        [InlineKeyboardButton("➡️ DM Us", url="https://t.me/m/SDmyGAMvNjY8")],
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/+A6f68ahZ-PhkOGQ0")]
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
