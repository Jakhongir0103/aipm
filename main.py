import os
import time
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from db import users_collection

# Load environment variables
load_dotenv()
telegram_api = os.environ.get('TELEGRAM_API')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def is_valid_token(deadline_token):
    """Validate if the token is from the current time interval"""
    try:
        print(deadline_token)
        # Convert base36 token back to timestamp
        deadline_token_timestamp = int(deadline_token, 36)
        print(deadline_token_timestamp)
        current_timestamp = int(time.time() * 1000)  # Convert to milliseconds
        print(current_timestamp)
        
        # Token is valid if it's from the current interval
        return current_timestamp < deadline_token_timestamp
    except ValueError:
        return False
    
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command and deep linking"""
    user_id = update.effective_user.id
    args = context.args  # This will contain any parameters passed with the start command
    
    # Initialize user in database if not exists
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({
            "user_id": user_id,
            "points": 0,
            "total_rewards": 0
        })
    
    # Create keyboard with Check Status button
    keyboard = [[InlineKeyboardButton("Check Status", callback_data='check_status')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Check if this is a QR code scan
    if args and args[0].startswith('order_'):
        # Extract token from the parameter
        try:
            token = args[0].split('_')[1]
            
            # Validate the token
            if is_valid_token(token):
                # Token is valid, process the order
                await process_order(update, context, reply_markup)
            else:
                # Token is expired
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="⚠️ This QR code has expired. Please scan the currently displayed QR code.",
                    reply_markup=reply_markup
                )
        except IndexError:
            # Invalid parameter format
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="⚠️ Invalid QR code format. Please try again.",
                reply_markup=reply_markup
            )
    else:
        # Regular start command
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Welcome to our Coffee Loyalty Program! Scan QR codes to earn points. Every 5 coffees = 1 free coffee!",
            reply_markup=reply_markup
        )

async def process_order(update: Update, context: ContextTypes.DEFAULT_TYPE, reply_markup: InlineKeyboardMarkup):
    """Process an order and update points"""
    user_id = update.effective_user.id
    user = users_collection.find_one({"user_id": user_id})
    current_points = user["points"]
    
    # Handle different point scenarios
    if current_points == 4:  # User has 4 points, this is their 5th coffee
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"points": 5}}
        )
        message = "Congratulations! You've earned a free coffee! 🎉 Use it on your next visit!"
    elif current_points == 5:  # User is redeeming their free coffee
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {"points": 0},
                "$inc": {"total_rewards": 1}
            }
        )
        message = "You've redeemed your free coffee! Counter has been reset. Start collecting again! ☕"
    else:  # Normal point accumulation
        users_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"points": 1}}
        )
        new_points = current_points + 1
        remaining = 5 - new_points
        message = f"You now have {new_points}/5 points! {remaining} more to go for a free coffee! ⭐"

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=reply_markup
    )

async def check_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Check Status button press"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user = users_collection.find_one({"user_id": user_id})
    
    # Create keyboard with Check Status button
    keyboard = [[InlineKeyboardButton("Check Status", callback_data='check_status')]]
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
            message = f"You currently have {points}/5 points. {remaining} more to go for a free coffee!\n\nTotal rewards earned: {total_rewards} ☕"
    
    # Include reply_markup in edit_message_text to keep the button
    try:
        await query.edit_message_text(
            text=message,
            reply_markup=reply_markup
        )
    except BadRequest as e:
        logger.info(f'Error occured in `check_status`. Skipping it...\n{e}')

def main():
    """Main function to run the bot"""
    application = ApplicationBuilder().token(telegram_api).build()
    
    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(check_status))
    
    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()