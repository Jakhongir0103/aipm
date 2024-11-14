import base64
import logging
import os
import time
from datetime import datetime, timedelta

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from pymongo import DESCENDING
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from db import user_points, user_transactions

# Load environment variables
load_dotenv()
telegram_api = os.environ["TELEGRAM_API"]
SECRET_KEY = os.environ["SECRET_TOKEN_ENCRYPTION_KEY"]
fernet = Fernet(SECRET_KEY.encode())

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def is_valid_token(token):
    """Validate if the token is from the current time interval"""
    try:
        # Decode base64 token
        encrypted_data = base64.urlsafe_b64decode(token.encode())
        # Decrypt the timestamp
        decrypted_timestamp = int(fernet.decrypt(encrypted_data).decode())
        current_timestamp = int(time.time())

        # Token is valid if current time is before deadline
        return current_timestamp < decrypted_timestamp
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return False


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command and deep linking"""
    user_id = update.effective_user.id
    args = (
        context.args
    )  # This will contain any parameters passed with the start command

    # Initialize user in database if not exists
    is_user = user_points.find_one({"user_id": user_id})
    print(is_user)
    if not is_user:
        user_points.insert_one({"user_id": user_id, "points": 0, "total_rewards": 0})
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                "🎉 Welcome to our Coffee Loyalty Program! 🎉\n"
                "Earn points by scanning QR codes with every coffee you buy!\n\n"
                "Every 5 coffees = 1 FREE coffee! 🎁\n\n"
                "Here's how it works:\n"
                "1️⃣ Scan the QR code at checkout to earn points!\n"
                "2️⃣ Collect 5 points and enjoy a FREE coffee on us! ☕️"
            ),
        )

    # Create keyboard with Check Status button
    keyboard = [[InlineKeyboardButton("Check Status", callback_data="check_status")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Check if this is a QR code scan
    if args and args[0].startswith("order_"):
        # Extract token from the parameter
        try:
            token = args[0].split("_")[1]

            # Validate the token
            if is_valid_token(token):
                # Fetch the latest transaction for the user
                last_transaction = user_transactions.find_one(
                    {"user_id": user_id}, sort=[("transaction_datetime", DESCENDING)]
                )

                if last_transaction:
                    last_transaction_time = last_transaction["transaction_datetime"]
                    current_time = datetime.now()

                    # Check if at least 1 minute has passed since the last scan
                    if current_time >= last_transaction_time + timedelta(minutes=1):
                        await process_order(update, context, reply_markup)
                    else:
                        await context.bot.send_message(
                            chat_id=update.effective_chat.id,
                            text="⚠️ You have already scanned this QR code. Please scan the newly displayed QR code after a few minutes.",
                            reply_markup=reply_markup,
                        )
                else:
                    # No previous transaction, so proceed with order processing
                    await process_order(update, context, reply_markup)
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="⚠️ This QR code has expired. Please scan the currently displayed QR code.",
                    reply_markup=reply_markup,
                )
        except IndexError:
            # Invalid parameter format
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Invalid QR code format. Please try again.",
                reply_markup=reply_markup,
            )
    else:
        # Regular start command
        if is_user:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Hope you are enjoying your Coffee with us! Every 5 coffees = 1 free coffee!",
                reply_markup=reply_markup,
            )


async def process_order(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    reply_markup: InlineKeyboardMarkup,
):
    """Process an order and update points"""
    user_id = update.effective_user.id
    user = user_points.find_one({"user_id": user_id})
    current_points = user["points"]

    # Handle different point scenarios
    if current_points == 4:  # User has 4 points, this is their 5th coffee
        user_points.update_one({"user_id": user_id}, {"$set": {"points": 5}})
        user_transactions.insert_one(
            {
                "user_id": user_id,
                "transaction_datetime": datetime.now(),
                "redeem": False,
            }
        )
        message = "Congratulations! You've earned a free coffee! 🎉 Use it on your next visit!"
    elif current_points == 5:  # User is redeeming their free coffee
        user_points.update_one(
            {"user_id": user_id}, {"$set": {"points": 0}, "$inc": {"total_rewards": 1}}
        )
        user_transactions.insert_one(
            {"user_id": user_id, "transaction_datetime": datetime.now(), "redeem": True}
        )
        message = "Enjoy your coffee! ☕️\n\nStart collecting again!"
    else:  # Normal point accumulation
        user_points.update_one({"user_id": user_id}, {"$inc": {"points": 1}})
        user_transactions.insert_one(
            {
                "user_id": user_id,
                "transaction_datetime": datetime.now(),
                "redeem": False,
            }
        )
        new_points = current_points + 1
        remaining = 5 - new_points
        message = f"You now have {new_points}/5 points! {remaining} more to go for a free coffee! ⭐"

    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=message, reply_markup=reply_markup
    )


async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Check Status button press"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user = user_points.find_one({"user_id": user_id})

    # Create keyboard with Check Status button
    keyboard = [[InlineKeyboardButton("Check Status", callback_data="check_status")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if not user:
        message = "You haven't started collecting points yet. Make your first purchase to begin!"
    else:
        points = user["points"]
        total_rewards = user["total_rewards"]
        remaining = 5 - points

        if points == 5:
            message = "You have a free coffee waiting! Visit us to redeem it! 🎉"
        else:
            message = f"You currently have {points}/5 points. {remaining} more to go for a free coffee!\n\nTotal number of coffees earned: {total_rewards} ☕"

    # Include reply_markup in edit_message_text to keep the button
    try:
        await query.edit_message_text(text=message, reply_markup=reply_markup)
    except BadRequest as e:
        logger.info(f"Error occured in `check_status`. Skipping it...\n{e}")


def main():
    """Main function to run the bot"""
    application = ApplicationBuilder().token(telegram_api).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(check_status))

    # Start the bot
    application.run_polling()


if __name__ == "__main__":
    main()
