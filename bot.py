import os
import json
import re
from pymongo import MongoClient
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters,
                          CallbackQueryHandler, ConversationHandler)
import random
import asyncio
import threading
from pymongo.errors import DuplicateKeyError

# Constants
ADMIN_ID = 6881713177  # Your admin ID
TELEGRAM_BOT_TOKEN = "7275717734:AAE6bq0Mdypn_wQL6F1wpphzEtLAco3_B3Y"
TELEGRAM_CHAT_ID = "6881713177"

# States for ConversationHandler
MAIN_MENU, REGISTER, PROFILE, REPORT_MENU, USERNAME_INPUT, REPORT_TYPE, IMPERSONATION_URL, REPORT_LOOP = range(8)
IG_LOGIN, IG_USERNAME, IG_PASSWORD = range(20, 23)

# Admin Panel States
ADMIN_PANEL, BROADCAST_MESSAGE, VIEW_USERS, USER_STATS = range(100, 104)

# Customizable settings
BOT_SETTINGS = {
    'font_style': 'HTML',
    'theme': 'premium',
    'emoji_style': 'full',
    'button_style': 'modern'
}

# Language strings
STRINGS = {
    'en': {
        'welcome': "🔥 <b>PREMIUM IG REPORTER V2.0</b> 🔥\n\n🎯 <b>Ultimate Instagram Mass Reporter</b>\n⚡ Lightning Fast • 🔒 100% Anonymous • 💯 Guaranteed Results\n\n🚀 <i>Join thousands of satisfied users!</i>",
        'main_menu': "🏠 <b>MAIN DASHBOARD</b>\n\n🎯 Choose your action:",
        'profile': "👤 <b>USER PROFILE</b>\n\n📊 Total Reports: <b>{reports}</b>\n⚡ Status: <b>PREMIUM USER</b>",
        'report_menu': "⚔️ <b>REPORT ATTACK CENTER</b>\n\n🎯 Ready to launch mass reports?",
        'send_username': "📱 <b>TARGET SELECTION</b>\n\n🎯 Enter Instagram username to report:\n\n⚠️ <b>Format:</b> @username\n❌ <b>No emojis allowed</b>\n\n<i>Example: @target_account</i>",
        'choose_report_type': "⚔️ <b>SELECT REPORT TYPE</b>\n\n🎯 Choose violation category:",
        'ask_impersonation_url': "🔗 <b>IMPERSONATION EVIDENCE</b>\n\n📎 Send URL of the original account (optional):",
        'confirm_start': "🚀 <b>ATTACK READY TO LAUNCH</b>\n\n🎯 Target: <b>@{username}</b>\n⚔️ Type: <b>{type}</b>",
        'reporting_started': "💥 <b>MASS REPORTING STARTED!</b>\n\n🎯 Target: <b>@{username}</b>\n⚡ Reports launching every 1-3 seconds...",
        'reporting_stopped': "⏹️ <b>ATTACK STOPPED</b>\n\n💥 Total strikes: <b>{total_strikes}</b>",
        'report_success': "✅ <b>STRIKE #{count} SUCCESSFUL</b>\n🎯 Target: <b>@{username}</b>",
        'report_failed': "❌ <b>STRIKE #{count} FAILED</b>\n🎯 Target: <b>@{username}</b>\n🔄 Retrying...",
        'invalid_username': "❌ <b>INVALID USERNAME</b>\n\n⚠️ Username must start with @ and contain only letters, numbers, dots, underscores",
        'admin_panel': "👑 <b>ADMIN CONTROL CENTER</b>\n\n🛠️ Administrator Dashboard",
        'user_stats': "📊 <b>BOT ANALYTICS</b>\n\n👥 Total Users: <b>{total}</b>",
        'user_list': "👥 <b>REGISTERED USERS</b>\n\n{users}",
        'broadcast_prompt': "📢 <b>BROADCAST MESSAGE</b>\n\nType message to send to all users:",
        'broadcast_sent': "✅ <b>Broadcast sent to {count} users!</b>",
        'my_reports': "📊 <b>MY REPORT HISTORY</b>\n\n{report_list}",
        'no_reports': "📭 <b>No reports found</b>",
        'settings_menu': "⚙️ <b>BOT SETTINGS</b>",
        'help_menu': "ℹ️ <b>HELP & SUPPORT</b>\n\nHow to use:\n1. Enter target username\n2. Choose report type\n3. Start reporting",
        'optional_login': "🔐 <b>OPTIONAL LOGIN</b>\n\n🌟 For enhanced features, you can login with Instagram\n\n📱 Enter Instagram username:",
        'login_canceled': "🔓 <b>Continuing without login</b>\n\nYou can still report accounts!"
    },
    'hi': {
        # Hindi translations would go here
    }
}

# Button texts
BUTTON_TEXTS = {
    'en': {
        'report_attack': '⚔️ Report Account',
        'profile': '👤 Profile',
        'my_reports': '📊 My Reports',
        'home': '🏠 Home',
        'admin_panel': '👑 Admin',
        'language': '🌐 Language',
        'help': 'ℹ️ Help',
        'settings': '⚙️ Settings',
        'start_new_report': '🚀 Start New Report',
        'stop_attack': '⏹️ Stop Attack',
        'login': '🔐 Login with IG',
        'continue_without_login': '🚫 Continue Without Login'
    },
    'hi': {
        # Hindi translations
    }
}

# Report types
REPORT_TYPES = {
    'hate': '😡 Hate Speech',
    'selfharm': '🆘 Self-Harm',
    'bully': '👊 Bullying',
    'impersonation': '🎭 Impersonation',
    'spam': '📧 Spam',
    'violence': '⚔️ Violence',
    'fake': '🚫 Fake Account'
}

# User session storage
sessions = {}
active_reports = {}
reporting_tasks = {}

# MongoDB connection
def get_db_connection():
    try:
        mongodb_uri = os.environ.get('MONGODB_URI', 'mongodb+srv://instaboost_user:uX1YzKjiOETNhyYj@cluster0.tolxjiz.mongodb.net/instaboost?retryWrites=true&w=majority&appName=Cluster0')
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        return client.instaboost
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def init_database():
    try:
        db = get_db_connection()
        if not db:
            return False
        
        # Create indexes
        try:
            db.users.create_index("user_id", unique=True)
            db.reports.create_index("user_id")
        except:
            pass
        
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

def save_user(user_id, user_data):
    try:
        db = get_db_connection()
        if not db:
            return False
        
        user_doc = {
            "user_id": user_id,
            "username": user_data.get('username', ''),
            "display_name": user_data.get('display_name', 'User'),
            "ig_username": user_data.get('ig_username', ''),
            "total_reports": user_data.get('total_reports', 0),
            "last_active": datetime.now()
        }
        
        db.users.update_one(
            {"user_id": user_id},
            {"$set": user_doc},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error saving user: {e}")
        return False

def get_user(user_id):
    try:
        db = get_db_connection()
        if not db:
            return None
        
        user = db.users.find_one({"user_id": user_id})
        if user:
            user.pop('_id', None)
            return user
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def update_user_reports(user_id, success=True):
    try:
        db = get_db_connection()
        if not db:
            return False
        
        if success:
            db.users.update_one(
                {"user_id": user_id},
                {"$inc": {"total_reports": 1}},
                upsert=True
            )
        return True
    except Exception as e:
        print(f"Error updating reports: {e}")
        return False

def validate_username(username):
    clean_username = username.replace('@', '')
    
    # Basic validation
    if not re.match(r'^[a-zA-Z0-9._]+$', clean_username):
        return False, "invalid_chars"
    
    if len(clean_username) < 1 or len(clean_username) > 30:
        return False, "invalid_length"
    
    return True, clean_username

def is_admin(user_id):
    return int(user_id) == ADMIN_ID

def get_main_keyboard(lang='en', is_admin_user=False):
    buttons = BUTTON_TEXTS[lang]
    
    keyboard = [
        [KeyboardButton(buttons['report_attack']), KeyboardButton(buttons['profile'])],
        [KeyboardButton(buttons['my_reports']), KeyboardButton(buttons['home'])]
    ]
    
    if is_admin_user:
        keyboard.append([KeyboardButton(buttons['admin_panel'])])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_report_keyboard(lang='en'):
    buttons = BUTTON_TEXTS[lang]
    return ReplyKeyboardMarkup([
        [KeyboardButton(buttons['start_new_report'])],
        [KeyboardButton("⬅️ Back"), KeyboardButton(buttons['home'])]
    ], resize_keyboard=True)

def get_attack_keyboard(lang='en'):
    buttons = BUTTON_TEXTS[lang]
    return ReplyKeyboardMarkup([
        [KeyboardButton(buttons['stop_attack'])],
        [KeyboardButton(buttons['home'])]
    ], resize_keyboard=True)

def get_login_keyboard(lang='en'):
    buttons = BUTTON_TEXTS[lang]
    return ReplyKeyboardMarkup([
        [KeyboardButton(buttons['login']), KeyboardButton(buttons['continue_without_login'])]
    ], resize_keyboard=True)

async def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    is_admin_user = is_admin(user_id)
    
    user_data = get_user(user_id)
    
    if not user_data:
        # New user - offer optional login
        await update.message.reply_text(
            STRINGS['en']['welcome'],
            parse_mode='HTML'
        )
        
        await asyncio.sleep(1)
        
        await update.message.reply_text(
            STRINGS['en']['optional_login'],
            reply_markup=get_login_keyboard('en'),
            parse_mode='HTML'
        )
        return REGISTER
    else:
        # Existing user
        lang = user_data.get('lang', 'en')
        await update.message.reply_text(
            STRINGS[lang]['main_menu'],
            reply_markup=get_main_keyboard(lang, is_admin_user),
            parse_mode='HTML'
        )
        return MAIN_MENU

async def handle_login_choice(update: Update, context: CallbackContext):
    text = update.message.text
    user_id = str(update.effective_user.id)
    
    if text == BUTTON_TEXTS['en']['login']:
        await update.message.reply_text(
            "📱 Please enter your Instagram username:"
        )
        return IG_USERNAME
    else:
        # Continue without login
        user_data = {
            "user_id": user_id,
            "username": update.effective_user.username or "User",
            "display_name": update.effective_user.first_name or "User",
            "total_reports": 0
        }
        save_user(user_id, user_data)
        
        await update.message.reply_text(
            STRINGS['en']['login_canceled'],
            reply_markup=get_main_keyboard('en', is_admin(user_id)),
            parse_mode='HTML'
        )
        return MAIN_MENU

async def handle_ig_username(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    ig_username = update.message.text.strip().replace('@', '')
    
    # Basic validation
    if not re.match(r'^[a-zA-Z0-9._]+$', ig_username):
        await update.message.reply_text(
            "❌ Invalid username format! Please enter a valid Instagram username."
        )
        return IG_USERNAME
    
    context.user_data['ig_username'] = ig_username
    
    await update.message.reply_text(
        "🔑 Please enter your Instagram password:"
    )
    return IG_PASSWORD

async def handle_ig_password(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    ig_username = context.user_data.get('ig_username', '')
    
    # Save user with IG credentials
    user_data = {
        "user_id": user_id,
        "username": update.effective_user.username or "User",
        "display_name": update.effective_user.first_name or "User",
        "ig_username": ig_username,
        "total_reports": 0
    }
    save_user(user_id, user_data)
    
    await update.message.reply_text(
        f"✅ Login successful! Welcome @{ig_username}",
        reply_markup=get_main_keyboard('en', is_admin(user_id)),
        parse_mode='HTML'
    )
    return MAIN_MENU

async def handle_main_menu(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = get_user(user_id) or {}
    lang = 'en'
    text = update.message.text
    buttons = BUTTON_TEXTS[lang]
    is_admin_user = is_admin(user_id)
    
    if text == buttons['report_attack']:
        await update.message.reply_text(
            STRINGS[lang]['report_menu'],
            reply_markup=get_report_keyboard(lang),
            parse_mode='HTML'
        )
        return REPORT_MENU
        
    elif text == buttons['profile']:
        reports = user_data.get('total_reports', 0)
        await update.message.reply_text(
            STRINGS[lang]['profile'].format(reports=reports),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif text == buttons['my_reports']:
        # Simplified for public access
        await update.message.reply_text(
            "📊 Your report history will appear here",
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif text == buttons['home']:
        await update.message.reply_text(
            STRINGS[lang]['main_menu'],
            reply_markup=get_main_keyboard(lang, is_admin_user),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif text == buttons['admin_panel'] and is_admin_user:
        return await admin_panel(update, context)
    
    return MAIN_MENU

async def handle_report_menu(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    lang = 'en'
    text = update.message.text
    buttons = BUTTON_TEXTS[lang]
    
    if text == buttons['start_new_report']:
        await update.message.reply_text(
            STRINGS[lang]['send_username'],
            parse_mode='HTML'
        )
        return USERNAME_INPUT
        
    elif text == "⬅️ Back":
        await update.message.reply_text(
            STRINGS[lang]['main_menu'],
            reply_markup=get_main_keyboard(lang, is_admin(user_id))),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif text == buttons['home']:
        await update.message.reply_text(
            STRINGS[lang]['main_menu'],
            reply_markup=get_main_keyboard(lang, is_admin(user_id))),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    return REPORT_MENU

async def handle_username_input(update: Update, context: CallbackContext):
    lang = 'en'
    username_input = update.message.text.strip()
    
    # Validate username
    is_valid, result = validate_username(username_input)
    
    if not is_valid:
        await update.message.reply_text(
            STRINGS[lang]['invalid_username'],
            parse_mode='HTML'
        )
        return USERNAME_INPUT
    
    # Add @ if not present
    username = result if username_input.startswith('@') else f"@{result}"
    context.user_data['target_username'] = username
    
    # Create report type buttons
    keyboard = []
    for key, value in REPORT_TYPES.items():
        keyboard.append([InlineKeyboardButton(value, callback_data=f'type_{key}')])
    
    await update.message.reply_text(
        STRINGS[lang]['choose_report_type'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return REPORT_TYPE

async def handle_report_type(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    lang = 'en'
    report_type = query.data.split('_')[1]
    
    context.user_data['report_type'] = report_type
    
    if report_type == 'impersonation':
        await query.edit_message_text(
            STRINGS[lang]['ask_impersonation_url'],
            parse_mode='HTML'
        )
        return IMPERSONATION_URL
    else:
        username = context.user_data['target_username']
        type_name = REPORT_TYPES[report_type]
        
        keyboard = [
            [InlineKeyboardButton("🚀 START REPORTING", callback_data='start_report')],
            [InlineKeyboardButton("❌ CANCEL", callback_data='cancel_report')]
        ]
        
        await query.edit_message_text(
            STRINGS[lang]['confirm_start'].format(username=username, type=type_name),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return REPORT_LOOP

async def handle_impersonation_url(update: Update, context: CallbackContext):
    lang = 'en'
    context.user_data['impersonation_url'] = update.message.text
    username = context.user_data['target_username']
    
    keyboard = [
        [InlineKeyboardButton("🚀 START REPORTING", callback_data='start_report')],
        [InlineKeyboardButton("❌ CANCEL", callback_data='cancel_report')]
    ]
    
    await update.message.reply_text(
        STRINGS[lang]['confirm_start'].format(username=username, type=REPORT_TYPES['impersonation']),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return REPORT_LOOP

async def handle_report_loop(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    lang = 'en'
    username = context.user_data.get('target_username', '')
    report_type = context.user_data.get('report_type', 'spam')
    
    if query.data == 'start_report':
        context.user_data['strike_count'] = 0
        
        # Create reporting task
        task = asyncio.create_task(
            start_reporting(context, user_id, username, report_type, lang)
        )
        reporting_tasks[user_id] = task
        
        await query.edit_message_text(
            STRINGS[lang]['reporting_started'].format(username=username),
            parse_mode='HTML'
        )
        
        # Change keyboard to attack mode
        await context.bot.send_message(
            chat_id=user_id,
            text="⚔️ Reporting in progress...",
            reply_markup=get_attack_keyboard(lang),
            parse_mode='HTML'
        )
        
    elif query.data == 'stop_report':
        # Cancel reporting task
        if user_id in reporting_tasks:
            reporting_tasks[user_id].cancel()
            del reporting_tasks[user_id]
        
        total_strikes = context.user_data.get('strike_count', 0)
        
        try:
            await query.edit_message_text(
                STRINGS[lang]['reporting_stopped'].format(total_strikes=total_strikes),
                parse_mode='HTML'
            )
        except:
            pass
        
        # Return to main menu
        await context.bot.send_message(
            chat_id=user_id,
            text=STRINGS[lang]['main_menu'],
            reply_markup=get_main_keyboard(lang, is_admin(user_id))),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif query.data == 'cancel_report':
        try:
            await query.edit_message_text(
                STRINGS[lang]['main_menu'],
                parse_mode='HTML'
            )
        except:
            pass
        
        await context.bot.send_message(
            chat_id=user_id,
            text=STRINGS[lang]['main_menu'],
            reply_markup=get_main_keyboard(lang, is_admin(user_id))),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    return REPORT_LOOP

async def handle_stop_attack(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    lang = 'en'
    
    # Cancel reporting task
    if user_id in reporting_tasks:
        reporting_tasks[user_id].cancel()
        del reporting_tasks[user_id]
    
    total_strikes = context.user_data.get('strike_count', 0)
    
    await update.message.reply_text(
        STRINGS[lang]['reporting_stopped'].format(total_strikes=total_strikes),
        parse_mode='HTML'
    )
    
    # Return to main menu
    await update.message.reply_text(
        STRINGS[lang]['main_menu'],
        reply_markup=get_main_keyboard(lang, is_admin(user_id))),
        parse_mode='HTML'
    )
    return MAIN_MENU

async def start_reporting(context: CallbackContext, user_id: str, username: str, report_type: str, lang: str):
    report_count = 0
    
    try:
        while True:
            report_count += 1
            context.user_data['strike_count'] = report_count
            
            # Random success/failure
            success_rate = random.choice([True, True, True, False])  # 75% success rate
            
            # Update user report count
            update_user_reports(user_id, success_rate)
            
            if success_rate:
                message = STRINGS[lang]['report_success'].format(count=report_count, username=username)
            else:
                message = STRINGS[lang]['report_failed'].format(count=report_count, username=username)
            
            # Send report status periodically
            if report_count % 3 == 1 or report_count <= 3:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML'
                )
            
            # Random delay
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Reporting error: {e}")

# Admin functions (only for you)
async def admin_panel(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return MAIN_MENU
    
    await update.message.reply_text(
        STRINGS['en']['admin_panel'],
        reply_markup=ReplyKeyboardMarkup([
            ["📢 Broadcast", "👥 Users"],
            ["📊 Statistics", "⬅️ Back"]
        ], resize_keyboard=True),
        parse_mode='HTML'
    )
    return ADMIN_PANEL

async def handle_admin_buttons(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return MAIN_MENU
    
    text = update.message.text
    
    if text == "⬅️ Back":
        await update.message.reply_text(
            STRINGS['en']['main_menu'],
            reply_markup=get_main_keyboard('en', True),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif text == "📢 Broadcast":
        await update.message.reply_text(
            STRINGS['en']['broadcast_prompt'],
            parse_mode='HTML'
        )
        return BROADCAST_MESSAGE
        
    elif text == "👥 Users":
        try:
            db = get_db_connection()
            users = list(db.users.find().limit(10))
            
            user_list = ""
            for user in users:
                user_list += f"👤 {user.get('display_name', 'User')} - 📊 {user.get('total_reports', 0)} reports\n"
            
            await update.message.reply_text(
                STRINGS['en']['user_list'].format(users=user_list),
                parse_mode='HTML'
            )
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
    
    elif text == "📊 Statistics":
        try:
            db = get_db_connection()
            total_users = db.users.count_documents({})
            total_reports = db.users.aggregate([{
                "$group": {"_id": None, "total": {"$sum": "$total_reports"}}
            }]).next().get('total', 0)
            
            await update.message.reply_text(
                STRINGS['en']['user_stats'].format(total=total_users) + f"\n📈 Total Reports: <b>{total_reports}</b>",
                parse_mode='HTML'
            )
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
    
    elif text == "🏠 Home":
        await update.message.reply_text(
            STRINGS['en']['main_menu'],
            reply_markup=get_main_keyboard('en', True),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    return ADMIN_PANEL

async def handle_broadcast(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    message = update.message.text
    try:
        db = get_db_connection()
        users = db.users.find()
        count = 0
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=f"📢 <b>ANNOUNCEMENT</b>\n\n{message}",
                    parse_mode='HTML'
                )
                count += 1
                await asyncio.sleep(0.2)
            except:
                pass
        
        await update.message.reply_text(
            STRINGS['en']['broadcast_sent'].format(count=count),
            parse_mode='HTML'
        )
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")
    
    return ADMIN_PANEL

def main():
    # Initialize database
    init_database()
    
    # Get bot token
    BOT_TOKEN = os.getenv("BOT_TOKEN", TELEGRAM_BOT_TOKEN)
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not found!")
        return

    try:
        print("🚀 Starting Public IG Reporter Bot...")
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        # Conversation handler
        conv = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                REGISTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login_choice)],
                IG_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ig_username)],
                IG_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ig_password)],
                MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu)],
                REPORT_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_report_menu)],
                USERNAME_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username_input)],
                REPORT_TYPE: [CallbackQueryHandler(handle_report_type, pattern='^type_')],
                IMPERSONATION_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_impersonation_url)],
                REPORT_LOOP: [
                    CallbackQueryHandler(handle_report_loop),
                    MessageHandler(filters.Regex(BUTTON_TEXTS['en']['stop_attack']), handle_stop_attack)
                ],
                ADMIN_PANEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_buttons)],
                BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast)]
            },
            fallbacks=[CommandHandler('start', start)],
            per_user=True
        )

        app.add_handler(conv)
        print("✅ Bot is ready!")
        
        # Production setup
        if os.environ.get('RENDER') or os.environ.get('PORT'):
            print("🌐 Production mode - Starting web server")
            
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import threading
            
            class HealthHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Bot is running')
            
            port = int(os.environ.get('PORT', 8000))
            server = HTTPServer(('0.0.0.0', port), HealthHandler)
            
            def run_server():
                print(f"Server running on port {port}")
                server.serve_forever()
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            app.run_polling(drop_pending_updates=True)
        else:
            print("💻 Development mode - Starting polling")
            app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
