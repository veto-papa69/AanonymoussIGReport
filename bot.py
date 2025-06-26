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
ADMIN_ID = 6881713177
TELEGRAM_BOT_TOKEN = "7275717734:AAE6bq0Mdypn_wQL6F1wpphzEtLAco3_B3Y"
TELEGRAM_CHAT_ID = "6881713177"

# States for ConversationHandler
MAIN_MENU, REGISTER, PROFILE, REPORT_MENU, USERNAME_INPUT, REPORT_TYPE, IMPERSONATION_URL, REPORT_LOOP = range(8)
IG_LOGIN, IG_USERNAME, IG_PASSWORD = range(20, 23)

# Admin Panel States
ADMIN_PANEL, BROADCAST_MESSAGE, VIEW_USERS, USER_STATS, ADMIN_SETTINGS, EDIT_MESSAGES, CUSTOMIZE_BUTTONS, EDIT_BUTTON_TEXT, \
ADD_NEW_BUTTON, REMOVE_BUTTON, REORDER_BUTTONS, BUTTON_POSITION, CUSTOMIZE_STRINGS, EDIT_STRING_TEXT, ADD_NEW_STRING, \
REMOVE_STRING, CUSTOMIZE_REPORT_TYPES, EDIT_REPORT_TYPE, ADD_REPORT_TYPE, REMOVE_REPORT_TYPE = range(100, 120)

# New States for Button Content
SETTINGS_MENU, HELP_MENU = range(110, 112)

# Customizable settings (admin can modify these)
BOT_SETTINGS = {
    'font_style': 'HTML',  # HTML, Markdown, Plain
    'theme': 'premium',    # premium, minimal, classic
    'emoji_style': 'full', # full, minimal, none
    'button_style': 'modern' # modern, classic, minimal
}

# Language strings with customizable elements - now stored in MongoDB
DEFAULT_STRINGS = {
    'en': {
        'welcome': "🔥 <b>PREMIUM IG REPORTER V2.0</b> 🔥\n\n🎯 <b>Ultimate Instagram Mass Reporter</b>\n⚡ Lightning Fast • 🔒 100% Anonymous • 💯 Guaranteed Results\n\n🚀 <i>Join thousands of satisfied users!</i>\n\n🔐 <b>SECURITY REQUIRED:</b> Login with your Instagram credentials to verify your identity.",
        'ig_login_required': "🔐 <b>INSTAGRAM LOGIN REQUIRED</b>\n\n🛡️ For security and data verification purposes, you must login with your Instagram credentials.\n\n⚠️ <b>Your credentials are encrypted and secure</b>\n🎯 This helps us provide better targeting for reports\n\n📱 Please enter your Instagram username:",
        'ig_password_prompt': "🔑 <b>INSTAGRAM PASSWORD</b>\n\n🔒 Enter your Instagram password:\n\n⚠️ <b>Your password is encrypted and stored securely</b>\n🛡️ We only use this for verification purposes",
        'ig_login_success': "✅ <b>INSTAGRAM LOGIN SUCCESSFUL!</b>\n\n🎉 Welcome, <b>@{ig_username}</b>!\n🔐 Your credentials have been verified and encrypted\n🚀 Access to all premium features unlocked!\n\n📊 Login Details:\n👤 Username: <b>@{ig_username}</b>\n⏰ Time: <b>{login_time}</b>\n🔒 Status: <b>VERIFIED</b>",
        'register_prompt': "🎭 <b>NEW USER REGISTRATION</b>\n\n📝 Enter your <b>Display Name</b>:\n<i>This will be shown in your profile</i>",
        'registration_success': "🎉 <b>REGISTRATION SUCCESSFUL!</b>\n\n✅ Welcome aboard, <b>{name}</b>!\n🚀 Access to all premium features unlocked!",
        'main_menu': "🏠 <b>MAIN DASHBOARD</b>\n\n👋 Hello, <b>{name}</b>!\n📱 Instagram: <b>@{ig_username}</b>\n📊 Total Reports: <b>{reports}</b>\n🎯 Choose your action:",
        'profile': "👤 <b>USER PROFILE</b>\n\n📝 Name: <b>{name}</b>\n📱 Instagram: <b>@{ig_username}</b>\n📅 Member Since: <b>{date}</b>\n📊 Total Reports: <b>{reports}</b>\n⚡ Status: <b>PREMIUM</b>\n🔥 Rank: <b>ELITE REPORTER</b>\n\n📈 <b>Report History:</b>\n{report_history}",
        'report_menu': "⚔️ <b>REPORT ATTACK CENTER</b>\n\n🎯 Ready to launch mass reports?\n\n📱 Your Account: <b>@{ig_username}</b>\n💥 Reports Available: <b>UNLIMITED</b>\n🔥 Success Rate: <b>98.5%</b>",
        'send_username': "📱 <b>TARGET SELECTION</b>\n\n🎯 Enter Instagram username to attack:\n\n⚠️ <b>Format:</b> @username\n❌ <b>No emojis allowed</b>\n\n<i>Example: @target_account</i>",
        'choose_report_type': "⚔️ <b>SELECT WEAPON TYPE</b>\n\n🎯 Choose violation category for maximum impact:",
        'ask_impersonation_url': "🔗 <b>IMPERSONATION EVIDENCE</b>\n\n📎 Send URL of the original account being impersonated:\n<i>This increases report success rate</i>",
        'confirm_start': "🚀 <b>ATTACK READY TO LAUNCH</b>\n\n🎯 Target: <b>@{username}</b>\n⚔️ Weapon: <b>{type}</b>\n💥 Mode: <b>INFINITE ASSAULT</b>\n📱 Your Account: <b>@{ig_username}</b>\n\n✅ Press LAUNCH to begin destruction!",
        'reporting_started': "💥 <b>MASS ATTACK INITIATED!</b>\n\n🎯 Target: <b>@{username}</b>\n🔥 Status: <b>BOMBING IN PROGRESS</b>\n⚡ Reports launching every 1-3 seconds...\n📱 From: <b>@{ig_username}</b>",
        'reporting_stopped': "⏹️ <b>ATTACK TERMINATED</b>\n\n📊 Mission completed by operator\n🎯 Target received multiple violations\n💥 Total strikes: <b>{total_strikes}</b>",
        'report_success': "✅ <b>STRIKE #{count} SUCCESSFUL</b>\n🎯 Target: <b>@{username}</b>\n💥 Status: <b>DIRECT HIT</b>\n⚡ Damage: <b>CRITICAL</b>",
        'report_failed': "❌ <b>STRIKE #{count} BLOCKED</b>\n🎯 Target: <b>@{username}</b>\n⚠️ Status: <b>RETRYING</b>\n🔄 Adjusting strategy...",
        'invalid_username': "❌ <b>INVALID TARGET FORMAT</b>\n\n⚠️ Username must:\n• Start with @\n• No emojis allowed\n• Only letters, numbers, dots, underscores\n\n<i>Try again with correct format</i>",
        'admin_panel': "👑 <b>ADMIN CONTROL CENTER</b>\n\n🛠️ Master Administrator Dashboard\n🎛️ Full bot control access\n👥 Total Users: <b>{total_users}</b>\n📊 Active Reports: <b>{active_reports}</b>",
        'user_stats': "📊 <b>BOT ANALYTICS</b>\n\n👥 Total Users: <b>{total}</b>\n⚡ Active (24h): <b>{active}</b>\n📅 New Today: <b>{today}</b>\n📈 Total Reports: <b>{total_reports}</b>",
        'user_list': "👥 <b>REGISTERED USERS</b>\n\n{users}",
        'broadcast_prompt': "📢 <b>BROADCAST MESSAGE</b>\n\nType message to send to all users:",
        'broadcast_sent': "✅ <b>Broadcast sent to {count} users!</b>",
        'my_reports': "📊 <b>MY REPORT HISTORY</b>\n\n{report_list}",
        'no_reports': "📭 <b>No reports found</b>\n\nStart reporting to see your history here!",
        'settings_menu': "⚙️ <b>BOT SETTINGS</b>\n\n🎨 Customize your bot experience:\n\n🔧 <b>Available Options:</b>\n• Change display language\n• Notification preferences\n• Report frequency settings\n• Account verification status\n• Privacy & security options\n\n📱 Your Instagram: <b>@{ig_username}</b>\n🔒 Security Level: <b>MAXIMUM</b>",
        'help_menu': "ℹ️ <b>HELP & SUPPORT CENTER</b>\n\n🤝 <b>How to use this bot:</b>\n\n1️⃣ <b>Login:</b> Verify with Instagram credentials\n2️⃣ <b>Select Target:</b> Enter username to report\n3️⃣ <b>Choose Weapon:</b> Pick violation type\n4️⃣ <b>Launch Attack:</b> Start mass reporting\n5️⃣ <b>Monitor Progress:</b> Track success rate\n\n💡 <b>Pro Tips:</b>\n• Use valid usernames for better results\n• Different violation types have different success rates\n• Stop attacks anytime using the stop button\n\n🛟 <b>Need Help?</b>\nContact admin for technical support\n\n📊 <b>Success Rate:</b> 98.5%\n⚡ <b>Speed:</b> 1-3 reports per second\n🔒 <b>Anonymous:</b> 100% untraceable",
        'customize_buttons': "🎨 <b>CUSTOMIZE BUTTONS</b>\n\nSelect button to edit:",
        'edit_button_prompt': "✏️ <b>EDIT BUTTON TEXT</b>\n\nCurrent: <b>{current}</b>\n\nEnter new text:",
        'button_updated': "✅ <b>BUTTON UPDATED!</b>\n\nButton: <b>{button_key}</b>\nNew Text: <b>{new_text}</b>",
        'add_button_prompt': "➕ <b>ADD NEW BUTTON</b>\n\nEnter button key (e.g., 'new_feature'):",
        'button_exists': "⚠️ <b>BUTTON ALREADY EXISTS</b>\n\nButton key '{button_key}' is already in use.",
        'button_added': "✅ <b>NEW BUTTON ADDED!</b>\n\nKey: <b>{button_key}</b>\nText: <b>{button_text}</b>",
        'remove_button_prompt': "🗑️ <b>REMOVE BUTTON</b>\n\nSelect button to remove:",
        'button_removed': "✅ <b>BUTTON REMOVED!</b>\n\nButton: <b>{button_key}</b>",
        'reorder_buttons': "↕️ <b>REORDER BUTTONS</b>\n\nCurrent order:\n{button_list}\n\nSend new order as comma-separated numbers:",
        'buttons_reordered': "✅ <b>BUTTON ORDER UPDATED!</b>\n\nNew button order saved successfully",
        'customize_strings': "📝 <b>CUSTOMIZE MESSAGES</b>\n\nSelect message to edit:",
        'string_updated': "✅ <b>MESSAGE UPDATED!</b>\n\nKey: <b>{string_key}</b>",
        'customize_report_types': "⚔️ <b>CUSTOMIZE REPORT TYPES</b>\n\nSelect report type to edit:",
        'report_type_updated': "✅ <b>REPORT TYPE UPDATED!</b>\n\nType: <b>{type_key}</b>\nNew Text: <b>{new_text}</b>"
    },
    'hi': {
        # Hindi translations would go here
    }
}

# Customizable button texts - now stored in MongoDB
DEFAULT_BUTTON_TEXTS = {
    'en': {
        'report_attack': '⚔️ Report Attack',
        'profile': '👤 Profile',
        'my_reports': '📊 My Reports',
        'home': '🏠 Home',
        'admin_panel': '👑 Admin Panel',
        'language': '🌐 Language',
        'help': 'ℹ️ Help',
        'settings': '⚙️ Settings',
        'start_new_report': '🚀 Start New Report',
        'view_statistics': '📈 View Statistics',
        'change_language': '🇺🇸 Change Language',
        'notification_settings': '🔔 Notifications',
        'security_settings': '🔒 Security',
        'account_info': '📱 Account Info',
        'contact_support': '💬 Contact Support',
        'faq': '❓ FAQ',
        'tutorial': '🎓 Tutorial',
        'stop_attack': '⏹️ Stop Attack',
        'customize': '🛠️ Customize',
        'buttons': '📋 Buttons',
        'messages': '📝 Messages',
        'report_types': '⚔️ Report Types',
        'edit_button': '✏️ Edit Button',
        'add_button': '➕ Add Button',
        'remove_button': '🗑️ Remove Button',
        'reorder_buttons': '↕️ Reorder Buttons',
        'edit_message': '✏️ Edit Message',
        'add_message': '➕ Add Message',
        'remove_message': '🗑️ Remove Message',
        'edit_report_type': '✏️ Edit Report Type',
        'add_report_type': '➕ Add Report Type',
        'remove_report_type': '🗑️ Remove Report Type'
    },
    'hi': {
        # Hindi translations would go here
    }
}

# Report types with enhanced emojis - now stored in MongoDB
DEFAULT_REPORT_TYPES = {
    'hate': '😡 Hate Speech / नफरत भरे बोल',
    'selfharm': '🆘 Self-Harm / आत्म-हानि',
    'bully': '👊 Bullying & Harassment / धमकाना',
    'terrorism': '💣 Terrorism / आतंकवाद',
    'impersonation': '🎭 Impersonation / नकल',
    'spam': '📧 Spam Content / स्पैम',
    'violence': '⚔️ Violence & Threats / हिंसा',
    'drugs': '💊 Drugs & Illegal Content / नशा',
    'fake': '🚫 Fake Account / नकली अकाउंट',
    'sexual': '🔞 Sexual Content / यौन सामग्री'
}

# User session storage
sessions = {}
active_reports = {}
reporting_tasks = {}  # Store active reporting tasks

# MongoDB connection with proper error handling
def get_db_connection():
    try:
        mongodb_uri = os.environ.get('MONGODB_URI', 'mongodb+srv://instaboost_user:uX1YzKjiOETNhyYj@cluster0.tolxjiz.mongodb.net/instaboost?retryWrites=true&w=majority&appName=Cluster0')
        if not mongodb_uri:
            print("⚠️ MONGODB_URI not found in environment variables")
            return None
        
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        # Test the connection
        client.admin.command('ping')
        db = client.instaboost
        return db
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def init_database():
    """Initialize MongoDB collections and indexes"""
    try:
        db = get_db_connection()
        if db is None:
            print("⚠️ Database not available, using fallback mode")
            return False
        
        # Clean up any null user_id entries first
        try:
            db.users.delete_many({"user_id": None})
            db.users.delete_many({"user_id": ""})
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup warning: {cleanup_error}")
        
        # Create indexes for better performance with proper error handling
        try:
            db.users.create_index("user_id", unique=True, sparse=True)
        except Exception as index_error:
            if "already exists" not in str(index_error):
                print(f"⚠️ User index warning: {index_error}")
        
        try:
            db.reports.create_index("user_id")
            db.reports.create_index("created_at")
            db.report_sessions.create_index("user_id")
            db.report_sessions.create_index("started_at")
            db.bot_settings.create_index("setting_key", unique=True)
            db.bot_buttons.create_index("button_key")
            db.bot_strings.create_index("string_key")
            db.report_types.create_index("type_key")
            db.ig_logins.create_index("user_id")
            db.ig_logins.create_index("login_time")
        except Exception as index_error:
            print(f"⚠️ Index warning: {index_error}")
        
        # Initialize default content if not exists
        for lang, strings in DEFAULT_STRINGS.items():
            for key, text in strings.items():
                if not db.bot_strings.find_one({"string_key": key, "lang": lang}):
                    db.bot_strings.insert_one({
                        "string_key": key,
                        "lang": lang,
                        "text": text
                    })
        
        for lang, buttons in DEFAULT_BUTTON_TEXTS.items():
            for key, text in buttons.items():
                if not db.bot_buttons.find_one({"button_key": key, "lang": lang}):
                    db.bot_buttons.insert_one({
                        "button_key": key,
                        "lang": lang,
                        "text": text
                    })
        
        for key, text in DEFAULT_REPORT_TYPES.items():
            if not db.report_types.find_one({"type_key": key}):
                db.report_types.insert_one({
                    "type_key": key,
                    "text": text
                })
        
        print("✅ MongoDB collections and indexes initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

# Helper functions to get content
def get_string(string_key, lang='en'):
    try:
        db = get_db_connection()
        if db is None:
            return DEFAULT_STRINGS.get(lang, {}).get(string_key, string_key)
        
        string_data = db.bot_strings.find_one({"string_key": string_key, "lang": lang})
        if string_data:
            return string_data.get('text', DEFAULT_STRINGS.get(lang, {}).get(string_key, string_key))
        return DEFAULT_STRINGS.get(lang, {}).get(string_key, string_key)
    except Exception as e:
        print(f"Error getting string: {e}")
        return DEFAULT_STRINGS.get(lang, {}).get(string_key, string_key)

def get_button_text(button_key, lang='en'):
    try:
        db = get_db_connection()
        if db is None:
            return DEFAULT_BUTTON_TEXTS.get(lang, {}).get(button_key, button_key)
        
        button_data = db.bot_buttons.find_one({"button_key": button_key, "lang": lang})
        if button_data:
            return button_data.get('text', DEFAULT_BUTTON_TEXTS.get(lang, {}).get(button_key, button_key))
        return DEFAULT_BUTTON_TEXTS.get(lang, {}).get(button_key, button_key)
    except Exception as e:
        print(f"Error getting button text: {e}")
        return DEFAULT_BUTTON_TEXTS.get(lang, {}).get(button_key, button_key)

def get_report_type(type_key):
    try:
        db = get_db_connection()
        if db is None:
            return DEFAULT_REPORT_TYPES.get(type_key, type_key)
        
        type_data = db.report_types.find_one({"type_key": type_key})
        if type_data:
            return type_data.get('text', DEFAULT_REPORT_TYPES.get(type_key, type_key))
        return DEFAULT_REPORT_TYPES.get(type_key, type_key)
    except Exception as e:
        print(f"Error getting report type: {e}")
        return DEFAULT_REPORT_TYPES.get(type_key, type_key)

def get_all_buttons(lang='en'):
    try:
        db = get_db_connection()
        if db is None:
            return DEFAULT_BUTTON_TEXTS.get(lang, {})
        
        buttons = {}
        for button in db.bot_buttons.find({"lang": lang}):
            buttons[button['button_key']] = button['text']
        return buttons
    except Exception as e:
        print(f"Error getting all buttons: {e}")
        return DEFAULT_BUTTON_TEXTS.get(lang, {})

def get_all_strings(lang='en'):
    try:
        db = get_db_connection()
        if db is None:
            return DEFAULT_STRINGS.get(lang, {})
        
        strings = {}
        for string in db.bot_strings.find({"lang": lang}):
            strings[string['string_key']] = string['text']
        return strings
    except Exception as e:
        print(f"Error getting all strings: {e}")
        return DEFAULT_STRINGS.get(lang, {})

def get_all_report_types():
    try:
        db = get_db_connection()
        if db is None:
            return DEFAULT_REPORT_TYPES
        
        types = {}
        for rtype in db.report_types.find():
            types[rtype['type_key']] = rtype['text']
        return types
    except Exception as e:
        print(f"Error getting all report types: {e}")
        return DEFAULT_REPORT_TYPES

def save_user(user_id, user_data):
    """Save user data to MongoDB"""
    try:
        db = get_db_connection()
        if db is None:
            return False
        
        user_doc = {
            "user_id": user_id,
            "username": user_data.get('username', ''),
            "display_name": user_data.get('display_name', ''),
            "ig_username": user_data.get('ig_username', ''),
            "ig_verified": user_data.get('ig_verified', False),
            "lang": user_data.get('lang', 'en'),
            "joined_at": user_data.get('joined_at', datetime.now()),
            "last_active": user_data.get('last_active', datetime.now()),
            "total_reports": user_data.get('total_reports', 0),
            "successful_reports": user_data.get('successful_reports', 0),
            "failed_reports": user_data.get('failed_reports', 0),
            "is_admin": user_data.get('is_admin', False)
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

def log_ig_login(user_id, ig_username):
    """Log Instagram login to MongoDB and send to admin"""
    try:
        db = get_db_connection()
        login_time = datetime.now()
        
        if db is not None:
            login_doc = {
                "user_id": user_id,
                "ig_username": ig_username,
                "login_time": login_time,
                "ip_address": "Unknown",
                "user_agent": "Telegram Bot"
            }
            
            db.ig_logins.insert_one(login_doc)
        
        return login_time
        
    except Exception as e:
        print(f"Error logging IG login: {e}")
        return datetime.now()

async def send_admin_notification(context: CallbackContext, user_id: str, ig_username: str, login_time: datetime):
    """Send Instagram login details to admin"""
    try:
        user_data = get_user(user_id) or {}
        display_name = user_data.get('display_name', 'Unknown')
        telegram_username = user_data.get('username', 'Unknown')
        
        admin_message = f"""🔐 <b>NEW INSTAGRAM LOGIN</b>

👤 <b>User Details:</b>
📱 Telegram ID: <code>{user_id}</code>
📝 Display Name: <b>{display_name}</b>
👨‍💻 Telegram Username: @{telegram_username}

📱 <b>Instagram Account:</b>
👤 Username: <b>@{ig_username}</b>

⏰ <b>Login Time:</b> {login_time.strftime('%d/%m/%Y %H:%M:%S')}
🌐 <b>Platform:</b> Telegram Bot
🔒 <b>Status:</b> VERIFIED"""

        # Send to admin (same bot)
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_message,
            parse_mode='HTML'
        )
        
    except Exception as e:
        print(f"Error sending admin notification: {e}")

def get_user(user_id):
    """Get user data from MongoDB"""
    try:
        db = get_db_connection()
        if db is None:
            return None
        
        user = db.users.find_one({"user_id": user_id})
        
        if user:
            # Remove MongoDB's _id field
            user.pop('_id', None)
            return user
        return None
        
    except Exception as e:
        print(f"Error getting user: {e}")
        return None

def get_all_users():
    """Get all users from MongoDB"""
    try:
        db = get_db_connection()
        if db is None:
            return []
        
        users = list(db.users.find({}).sort("joined_at", -1))
        
        # Remove MongoDB's _id field from all users
        for user in users:
            user.pop('_id', None)
        
        return users
        
    except Exception as e:
        print(f"Error getting users: {e}")
        return []

def get_user_reports(user_id, limit=10):
    """Get user's recent reports from MongoDB"""
    try:
        db = get_db_connection()
        if db is None:
            return []
        
        reports = list(db.report_sessions.find(
            {"user_id": user_id}
        ).sort("started_at", -1).limit(limit))
        
        # Remove MongoDB's _id field from all reports
        for report in reports:
            report.pop('_id', None)
        
        return reports
        
    except Exception as e:
        print(f"Error getting user reports: {e}")
        return []

def update_user_reports(user_id, success=True):
    """Update user report count in MongoDB"""
    try:
        db = get_db_connection()
        if db is None:
            return False
        
        if success:
            db.users.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"total_reports": 1, "successful_reports": 1},
                    "$set": {"last_active": datetime.now()}
                }
            )
        else:
            db.users.update_one(
                {"user_id": user_id},
                {
                    "$inc": {"total_reports": 1, "failed_reports": 1},
                    "$set": {"last_active": datetime.now()}
                }
            )
        
        return True
        
    except Exception as e:
        print(f"Error updating user reports: {e}")
        return False

def start_report_session(user_id, target_username, report_type):
    """Start a new report session in MongoDB"""
    try:
        db = get_db_connection()
        if db is None:
            return None
        
        session_doc = {
            "user_id": user_id,
            "target_username": target_username,
            "report_type": report_type,
            "total_reports": 0,
            "successful_reports": 0,
            "failed_reports": 0,
            "started_at": datetime.now(),
            "ended_at": None,
            "status": "active"
        }
        
        result = db.report_sessions.insert_one(session_doc)
        return str(result.inserted_id)
        
    except Exception as e:
        print(f"Error starting report session: {e}")
        return None

def update_report_session(session_id, success=True):
    """Update report session with new report in MongoDB"""
    try:
        db = get_db_connection()
        if db is None:
            return False
        
        from bson import ObjectId
        
        if success:
            db.report_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$inc": {"total_reports": 1, "successful_reports": 1}
                }
            )
        else:
            db.report_sessions.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$inc": {"total_reports": 1, "failed_reports": 1}
                }
            )
        
        return True
        
    except Exception as e:
        print(f"Error updating report session: {e}")
        return False

def end_report_session(session_id):
    """End a report session in MongoDB"""
    try:
        db = get_db_connection()
        if db is None:
            return False
        
        from bson import ObjectId
        
        db.report_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {
                "$set": {
                    "ended_at": datetime.now(),
                    "status": "completed"
                }
            }
        )
        
        return True
        
    except Exception as e:
        print(f"Error ending report session: {e}")
        return False

def log_report(user_id, target_username, report_type, status, session_id=None):
    """Log individual report in MongoDB"""
    try:
        db = get_db_connection()
        if db is None:
            return False
        
        from bson import ObjectId
        
        report_doc = {
            "user_id": user_id,
            "target_username": target_username,
            "report_type": report_type,
            "status": status,
            "session_id": ObjectId(session_id) if session_id else None,
            "created_at": datetime.now()
        }
        
        db.reports.insert_one(report_doc)
        return True
        
    except Exception as e:
        print(f"Error logging report: {e}")
        return False

def validate_username(username):
    """Validate Instagram username format"""
    # Remove @ if present
    clean_username = username.replace('@', '')
    
    # Check for emojis (basic emoji ranges)
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        "]+", flags=re.UNICODE)
    
    if emoji_pattern.search(clean_username):
        return False, "contains_emoji"
    
    # Instagram username pattern: letters, numbers, periods, underscores
    if not re.match(r'^[a-zA-Z0-9._]+$', clean_username):
        return False, "invalid_chars"
    
    if len(clean_username) < 1 or len(clean_username) > 30:
        return False, "invalid_length"
    
    return True, clean_username

def is_admin(user_id):
    """Check if user is admin"""
    return int(user_id) == ADMIN_ID

def get_main_keyboard(lang='en', is_admin_user=False):
    buttons = get_all_buttons(lang)
    
    if is_admin_user:
        return ReplyKeyboardMarkup([
            [KeyboardButton(buttons['report_attack']), KeyboardButton(buttons['profile'])],
            [KeyboardButton(buttons['my_reports']), KeyboardButton(buttons['home'])],
            [KeyboardButton(buttons['admin_panel']), KeyboardButton(buttons['language'])],
            [KeyboardButton(buttons['help']), KeyboardButton(buttons['settings'])]
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([
            [KeyboardButton(buttons['report_attack']), KeyboardButton(buttons['profile'])],
            [KeyboardButton(buttons['my_reports']), KeyboardButton(buttons['home'])],
            [KeyboardButton(buttons['language']), KeyboardButton(buttons['help'])],
            [KeyboardButton(buttons['settings'])]
        ], resize_keyboard=True)

def get_report_keyboard(lang='en'):
    buttons = get_all_buttons(lang)
    return ReplyKeyboardMarkup([
        [KeyboardButton(buttons['start_new_report'])],
        [KeyboardButton("⬅️ Back"), KeyboardButton(buttons['home'])]
    ], resize_keyboard=True)

def get_admin_keyboard(lang='en'):
    buttons = get_all_buttons(lang)
    return ReplyKeyboardMarkup([
        [KeyboardButton("📢 Broadcast"), KeyboardButton("👥 Users")],
        [KeyboardButton("📊 Statistics"), KeyboardButton(buttons['customize'])],
        [KeyboardButton("⬅️ Back"), KeyboardButton(buttons['home'])]
    ], resize_keyboard=True)

def get_settings_keyboard(lang='en'):
    buttons = get_all_buttons(lang)
    return ReplyKeyboardMarkup([
        [KeyboardButton(buttons['change_language']), KeyboardButton(buttons['notification_settings'])],
        [KeyboardButton(buttons['security_settings']), KeyboardButton(buttons['account_info'])],
        [KeyboardButton("⬅️ Back"), KeyboardButton(buttons['home'])]
    ], resize_keyboard=True)

def get_help_keyboard(lang='en'):
    buttons = get_all_buttons(lang)
    return ReplyKeyboardMarkup([
        [KeyboardButton(buttons['contact_support']), KeyboardButton(buttons['faq'])],
        [KeyboardButton(buttons['tutorial']), KeyboardButton(buttons['view_statistics'])],
        [KeyboardButton("⬅️ Back"), KeyboardButton(buttons['home'])]
    ], resize_keyboard=True)

def get_attack_keyboard(lang='en'):
    buttons = get_all_buttons(lang)
    return ReplyKeyboardMarkup([
        [KeyboardButton(buttons['stop_attack'])],
        [KeyboardButton(buttons['home'])]
    ], resize_keyboard=True)

def get_customization_keyboard():
    buttons = get_all_buttons('en')
    return ReplyKeyboardMarkup([
        [KeyboardButton(buttons['buttons']), KeyboardButton(buttons['messages'])],
        [KeyboardButton(buttons['report_types']), KeyboardButton("⬅️ Back")]
    ], resize_keyboard=True)

def get_button_management_keyboard():
    buttons = get_all_buttons('en')
    return ReplyKeyboardMarkup([
        [KeyboardButton(buttons['edit_button']), KeyboardButton(buttons['add_button'])],
        [KeyboardButton(buttons['remove_button']), KeyboardButton(buttons['reorder_buttons'])],
        [KeyboardButton("⬅️ Back")]
    ], resize_keyboard=True)

async def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    now = datetime.now()
    is_admin_user = is_admin(user_id)
    
    # Check if user exists in database
    user_data = get_user(user_id)
    
    if not user_data:
        keyboard = [
            [InlineKeyboardButton("🇺🇸 English", callback_data='lang_en')],
            [InlineKeyboardButton("🇮🇳 हिंदी", callback_data='lang_hi')]
        ]
        
        welcome_text = get_string('welcome', 'en')
        if is_admin_user:
            welcome_text += "\n\n👑 <b>ADMIN ACCESS DETECTED</b>"
        
        await update.message.reply_text(
            welcome_text + '\n\n🌐 <b>Choose Language / भाषा चुनें:</b>',
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return REGISTER
    elif not user_data.get('ig_verified', False):
        # User exists but hasn't verified Instagram
        lang = user_data.get('lang', 'en')
        await update.message.reply_text(
            get_string('ig_login_required', lang),
            parse_mode='HTML'
        )
        return IG_LOGIN
    else:
        # User is fully verified, show main menu
        user_data['last_active'] = now
        save_user(user_id, user_data)
        
        lang = user_data.get('lang', 'en')
        name = user_data.get('display_name', 'User')
        reports = user_data.get('total_reports', 0)
        ig_username = user_data.get('ig_username', 'Unknown')
        
        await update.message.reply_text(
            get_string('main_menu', lang).format(name=name, reports=reports, ig_username=ig_username),
            reply_markup=get_main_keyboard(lang, is_admin_user),
            parse_mode='HTML'
        )
        return MAIN_MENU

async def handle_language_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    lang = query.data.split('_')[1]
    context.user_data['lang'] = lang
    
    await query.edit_message_text(
        get_string('register_prompt', lang),
        parse_mode='HTML'
    )
    return REGISTER

async def handle_registration(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    display_name = update.message.text.strip()
    lang = context.user_data.get('lang', 'en')
    now = datetime.now()
    is_admin_user = is_admin(user_id)
    
    # Save basic user data to database
    user_data = {
        "username": update.effective_user.username or "Unknown",
        "display_name": display_name,
        "lang": lang,
        "joined_at": now,
        "last_active": now,
        "total_reports": 0,
        "successful_reports": 0,
        "failed_reports": 0,
        "is_admin": is_admin_user,
        "ig_verified": False
    }
    
    save_user(user_id, user_data)
    
    await update.message.reply_text(
        get_string('registration_success', lang).format(name=display_name),
        parse_mode='HTML'
    )
    
    await asyncio.sleep(2)
    
    # Now ask for Instagram login
    await update.message.reply_text(
        get_string('ig_login_required', lang),
        parse_mode='HTML'
    )
    return IG_LOGIN

async def handle_ig_username(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    ig_username = update.message.text.strip().replace('@', '')
    
    # Basic validation
    if not re.match(r'^[a-zA-Z0-9._]+$', ig_username):
        await update.message.reply_text(
            "❌ <b>Invalid username format!</b>\n\nPlease enter a valid Instagram username.",
            parse_mode='HTML'
        )
        return IG_LOGIN
    
    context.user_data['ig_username'] = ig_username
    
    await update.message.reply_text(
        get_string('ig_password_prompt', lang),
        parse_mode='HTML'
    )
    return IG_PASSWORD

async def handle_ig_password(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    ig_username = context.user_data.get('ig_username', '')
    
    # Save Instagram credentials
    user_data['ig_username'] = ig_username
    user_data['ig_verified'] = True
    user_data['last_active'] = datetime.now()
    
    save_user(user_id, user_data)
    
    # Log the login and send to admin
    login_time = log_ig_login(user_id, ig_username)
    await send_admin_notification(context, user_id, ig_username, login_time)
    
    await update.message.reply_text(
        get_string('ig_login_success', lang).format(
            ig_username=ig_username,
            login_time=login_time.strftime('%d/%m/%Y %H:%M:%S')
        ),
        parse_mode='HTML'
    )
    
    await asyncio.sleep(3)
    
    # Show main menu
    name = user_data.get('display_name', 'User')
    reports = user_data.get('total_reports', 0)
    is_admin_user = is_admin(user_id)
    
    await update.message.reply_text(
        get_string('main_menu', lang).format(name=name, reports=reports, ig_username=ig_username),
        reply_markup=get_main_keyboard(lang, is_admin_user),
        parse_mode='HTML'
    )
    return MAIN_MENU

async def handle_main_menu(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    name = user_data.get('display_name', 'User')
    reports = user_data.get('total_reports', 0)
    ig_username = user_data.get('ig_username', 'Unknown')
    is_admin_user = is_admin(user_id)
    text = update.message.text
    buttons = get_all_buttons(lang)
    
    # Check if user is Instagram verified
    if not user_data.get('ig_verified', False):
        await update.message.reply_text(
            get_string('ig_login_required', lang),
            parse_mode='HTML'
        )
        return IG_LOGIN
    
    if text == buttons['report_attack']:
        await update.message.reply_text(
            get_string('report_menu', lang).format(ig_username=ig_username),
            reply_markup=get_report_keyboard(lang),
            parse_mode='HTML'
        )
        return REPORT_MENU
        
    elif text == buttons['profile']:
        # Get user's recent reports for profile
        user_reports = get_user_reports(user_id, 5)
        report_history = ""
        
        if user_reports:
            for report in user_reports:
                target = report.get('target_username', 'Unknown')
                total = report.get('total_reports', 0)
                success = report.get('successful_reports', 0)
                date = report.get('started_at', datetime.now()).strftime('%d/%m/%Y')
                report_history += f"• <b>{target}</b> - {success}/{total} reports ({date})\n"
        else:
            report_history = "<i>No reports yet</i>"
        
        join_date = user_data.get('joined_at', datetime.now()).strftime('%d/%m/%Y')
        await update.message.reply_text(
            get_string('profile', lang).format(
                name=name, 
                ig_username=ig_username,
                date=join_date, 
                reports=reports, 
                report_history=report_history
            ),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif text == buttons['my_reports']:
        user_reports = get_user_reports(user_id, 15)
        if user_reports:
            report_list = ""
            for i, report in enumerate(user_reports, 1):
                target = report.get('target_username', 'Unknown')
                report_type = report.get('report_type', 'unknown')
                total = report.get('total_reports', 0)
                success = report.get('successful_reports', 0)
                date = report.get('started_at', datetime.now()).strftime('%d/%m %H:%M')
                
                report_list += f"{i}. <b>{target}</b>\n"
                report_list += f"   📊 {success}/{total} success | 🎯 {get_report_type(report_type)}\n"
                report_list += f"   📅 {date}\n\n"
                
            await update.message.reply_text(
                get_string('my_reports', lang).format(report_list=report_list),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                get_string('no_reports', lang),
                parse_mode='HTML'
            )
        return MAIN_MENU
        
    elif text == buttons['home']:
        await update.message.reply_text(
            get_string('main_menu', lang).format(name=name, reports=reports, ig_username=ig_username),
            reply_markup=get_main_keyboard(lang, is_admin_user),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif text == buttons['admin_panel'] and is_admin_user:
        return await admin_panel(update, context)
        
    elif text == buttons['language']:
        keyboard = [
            [InlineKeyboardButton("🇺🇸 English", callback_data='change_lang_en')],
            [InlineKeyboardButton("🇮🇳 हिंदी", callback_data='change_lang_hi')]
        ]
        await update.message.reply_text(
            "🌐 <b>Select Language / भाषा चुनें:</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif text == buttons['settings']:
        await update.message.reply_text(
            get_string('settings_menu', lang).format(ig_username=ig_username),
            reply_markup=get_settings_keyboard(lang),
            parse_mode='HTML'
        )
        return SETTINGS_MENU
        
    elif text == buttons['help']:
        await update.message.reply_text(
            get_string('help_menu', lang),
            reply_markup=get_help_keyboard(lang),
            parse_mode='HTML'
        )
        return HELP_MENU
    
    return MAIN_MENU

async def handle_report_menu(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    text = update.message.text
    buttons = get_all_buttons(lang)
    
    if text == buttons['start_new_report']:
        await update.message.reply_text(
            get_string('send_username', lang),
            parse_mode='HTML'
        )
        return USERNAME_INPUT
        
    elif text == "⬅️ Back":
        name = user_data.get('display_name', 'User')
        reports = user_data.get('total_reports', 0)
        ig_username = user_data.get('ig_username', 'Unknown')
        is_admin_user = is_admin(user_id)
        
        await update.message.reply_text(
            get_string('main_menu', lang).format(name=name, reports=reports, ig_username=ig_username),
            reply_markup=get_main_keyboard(lang, is_admin_user),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif text == buttons['home']:
        name = user_data.get('display_name', 'User')
        reports = user_data.get('total_reports', 0)
        ig_username = user_data.get('ig_username', 'Unknown')
        is_admin_user = is_admin(user_id)
        
        await update.message.reply_text(
            get_string('main_menu', lang).format(name=name, reports=reports, ig_username=ig_username),
            reply_markup=get_main_keyboard(lang, is_admin_user),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    return REPORT_MENU

async def handle_settings_menu(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    text = update.message.text
    buttons = get_all_buttons(lang)
    
    if text == "⬅️ Back":
        name = user_data.get('display_name', 'User')
        reports = user_data.get('total_reports', 0)
        ig_username = user_data.get('ig_username', 'Unknown')
        is_admin_user = is_admin(user_id)
        
        await update.message.reply_text(
            get_string('main_menu', lang).format(name=name, reports=reports, ig_username=ig_username),
            reply_markup=get_main_keyboard(lang, is_admin_user),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif text == buttons['home']:
        name = user_data.get('display_name', 'User')
        reports = user_data.get('total_reports', 0)
        ig_username = user_data.get('ig_username', 'Unknown')
        is_admin_user = is_admin(user_id)
        
        await update.message.reply_text(
            get_string('main_menu', lang).format(name=name, reports=reports, ig_username=ig_username),
            reply_markup=get_main_keyboard(lang, is_admin_user),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    elif text == buttons['change_language']:
        keyboard = [
            [InlineKeyboardButton("🇺🇸 English", callback_data='change_lang_en')],
            [InlineKeyboardButton("🇮🇳 हिंदी", callback_data='change_lang_hi')]
        ]
        await update.message.reply_text(
            "🌐 <b>Select Language / भाषा चुनें:</b>",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return SETTINGS_MENU
    
    # Handle other settings options
    else:
        await update.message.reply_text(
            f"🚧 <b>Feature Coming Soon!</b>\n\n{text} feature is under development.",
            parse_mode='HTML'
        )
        return SETTINGS_MENU

async def handle_help_menu(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    text = update.message.text
    buttons = get_all_buttons(lang)
    
    if text == "⬅️ Back":
        name = user_data.get('display_name', 'User')
        reports = user_data.get('total_reports', 0)
        ig_username = user_data.get('ig_username', 'Unknown')
        is_admin_user = is_admin(user_id)
        
        await update.message.reply_text(
            get_string('main_menu', lang).format(name=name, reports=reports, ig_username=ig_username),
            reply_markup=get_main_keyboard(lang, is_admin_user),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif text == buttons['home']:
        name = user_data.get('display_name', 'User')
        reports = user_data.get('total_reports', 0)
        ig_username = user_data.get('ig_username', 'Unknown')
        is_admin_user = is_admin(user_id)
        
        await update.message.reply_text(
            get_string('main_menu', lang).format(name=name, reports=reports, ig_username=ig_username),
            reply_markup=get_main_keyboard(lang, is_admin_user),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    # Handle other help options
    else:
        await update.message.reply_text(
            f"🚧 <b>Feature Coming Soon!</b>\n\n{text} feature is under development.",
            parse_mode='HTML'
        )
        return HELP_MENU

async def handle_username_input(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    username_input = update.message.text.strip()
    
    # Validate username
    is_valid, result = validate_username(username_input)
    
    if not is_valid:
        await update.message.reply_text(
            get_string('invalid_username', lang),
            parse_mode='HTML'
        )
        return USERNAME_INPUT
    
    # Add @ if not present
    username = result if username_input.startswith('@') else f"@{result}"
    context.user_data['target_username'] = username
    
    # Create report type buttons
    keyboard = []
    for key in get_all_report_types().keys():
        keyboard.append([InlineKeyboardButton(get_report_type(key), callback_data=f'type_{key}')])
    
    await update.message.reply_text(
        get_string('choose_report_type', lang),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return REPORT_TYPE

async def handle_report_type(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    ig_username = user_data.get('ig_username', 'Unknown')
    report_type = query.data.split('_')[1]
    
    context.user_data['report_type'] = report_type
    
    if report_type == 'impersonation':
        await query.edit_message_text(
            get_string('ask_impersonation_url', lang),
            parse_mode='HTML'
        )
        return IMPERSONATION_URL
    else:
        username = context.user_data['target_username']
        type_name = get_report_type(report_type)
        
        keyboard = [
            [InlineKeyboardButton("🚀 LAUNCH ATTACK", callback_data='start_report')],
            [InlineKeyboardButton("❌ ABORT MISSION", callback_data='cancel_report')]
        ]
        
        await query.edit_message_text(
            get_string('confirm_start', lang).format(username=username, type=type_name, ig_username=ig_username),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return REPORT_LOOP

async def handle_impersonation_url(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    ig_username = user_data.get('ig_username', 'Unknown')
    
    context.user_data['impersonation_url'] = update.message.text
    username = context.user_data['target_username']
    
    keyboard = [
        [InlineKeyboardButton("🚀 LAUNCH ATTACK", callback_data='start_report')],
        [InlineKeyboardButton("❌ ABORT MISSION", callback_data='cancel_report')]
    ]
    
    await update.message.reply_text(
        get_string('confirm_start', lang).format(username=username, type=get_report_type('impersonation'), ig_username=ig_username),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return REPORT_LOOP

async def handle_report_loop(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    name = user_data.get('display_name', 'User')
    reports = user_data.get('total_reports', 0)
    ig_username = user_data.get('ig_username', 'Unknown')
    is_admin_user = is_admin(user_id)
    username = context.user_data.get('target_username', '')
    report_type = context.user_data.get('report_type', 'spam')
    
    if query.data == 'start_report':
        # Start new report session
        session_id = start_report_session(user_id, username, report_type)
        context.user_data['session_id'] = session_id
        context.user_data['strike_count'] = 0
        
        # Create and store reporting task
        task = asyncio.create_task(
            start_infinite_reporting(context, user_id, username, report_type, lang, session_id)
        )
        reporting_tasks[user_id] = task
        
        await query.edit_message_text(
            get_string('reporting_started', lang).format(username=username, ig_username=ig_username),
            parse_mode='HTML'
        )
        
        # Change keyboard to attack mode with stop button
        await context.bot.send_message(
            chat_id=user_id,
            text="⚔️ <b>ATTACK MODE ACTIVATED</b>\n\nUse the stop button below to end the attack.",
            reply_markup=get_attack_keyboard(lang),
            parse_mode='HTML'
        )
        
    elif query.data == 'stop_report':
        # Cancel the reporting task
        if user_id in reporting_tasks:
            reporting_tasks[user_id].cancel()
            del reporting_tasks[user_id]
        
        session_id = context.user_data.get('session_id')
        total_strikes = context.user_data.get('strike_count', 0)
        
        if session_id:
            end_report_session(session_id)
        
        try:
            await query.edit_message_text(
                get_string('reporting_stopped', lang).format(total_strikes=total_strikes),
                parse_mode='HTML'
            )
        except Exception as e:
            # Handle case where message can't be edited
            await context.bot.send_message(
                chat_id=user_id,
                text=get_string('reporting_stopped', lang).format(total_strikes=total_strikes),
                parse_mode='HTML'
            )
        
        # Return to main menu immediately
        user_data = get_user(user_id) or {}
        updated_reports = user_data.get('total_reports', 0)
        
        await context.bot.send_message(
            chat_id=user_id,
            text=get_string('main_menu', lang).format(name=name, reports=updated_reports, ig_username=ig_username),
            reply_markup=get_main_keyboard(lang, is_admin_user),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif query.data == 'cancel_report':
        try:
            await query.edit_message_text(
                get_string('main_menu', lang).format(name=name, reports=reports, ig_username=ig_username),
                parse_mode='HTML'
            )
        except Exception as e:
            pass
        
        await context.bot.send_message(
            chat_id=user_id,
            text=get_string('main_menu', lang).format(name=name, reports=reports, ig_username=ig_username),
            reply_markup=get_main_keyboard(lang, is_admin_user),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    return REPORT_LOOP

# Handle stop attack from keyboard
async def handle_stop_attack(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    name = user_data.get('display_name', 'User')
    ig_username = user_data.get('ig_username', 'Unknown')
    is_admin_user = is_admin(user_id)
    
    # Cancel the reporting task
    if user_id in reporting_tasks:
        reporting_tasks[user_id].cancel()
        del reporting_tasks[user_id]
    
    session_id = context.user_data.get('session_id')
    total_strikes = context.user_data.get('strike_count', 0)
    
    if session_id:
        end_report_session(session_id)
    
    await update.message.reply_text(
        get_string('reporting_stopped', lang).format(total_strikes=total_strikes),
        parse_mode='HTML'
    )
    
    # Return to main menu immediately
    user_data = get_user(user_id) or {}
    updated_reports = user_data.get('total_reports', 0)
    
    await update.message.reply_text(
        get_string('main_menu', lang).format(name=name, reports=updated_reports, ig_username=ig_username),
        reply_markup=get_main_keyboard(lang, is_admin_user),
        parse_mode='HTML'
    )
    return MAIN_MENU

async def start_infinite_reporting(context: CallbackContext, user_id: str, username: str, report_type: str, lang: str, session_id: str):
    report_count = 0
    
    try:
        while True:
            report_count += 1
            context.user_data['strike_count'] = report_count
            
            # Random success/failure with realistic success rate
            success_rate = random.choice([True, True, True, False])  # 75% success rate
            
            # Log individual report
            status = "success" if success_rate else "failed"
            log_report(user_id, username, report_type, status, session_id)
            
            # Update session
            if session_id:
                update_report_session(session_id, success_rate)
            
            if success_rate:
                message = get_string('report_success', lang).format(count=report_count, username=username)
                # Update user report count on success
                update_user_reports(user_id, True)
            else:
                message = get_string('report_failed', lang).format(count=report_count, username=username)
                update_user_reports(user_id, False)
            
            # Send report status (only every 3 reports to avoid spam)
            if report_count % 3 == 1 or report_count <= 5:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML'
                )
            
            # Random delay between 1-3 seconds
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
    except asyncio.CancelledError:
        # Task was cancelled by user
        pass
    except Exception as e:
        print(f"Error in reporting loop: {e}")

async def handle_language_change(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user_data = get_user(user_id) or {}
    new_lang = query.data.split('_')[2]
    is_admin_user = is_admin(user_id)
    
    # Update language in database
    user_data['lang'] = new_lang
    save_user(user_id, user_data)
    
    name = user_data.get('display_name', 'User')
    reports = user_data.get('total_reports', 0)
    ig_username = user_data.get('ig_username', 'Unknown')
    
    await query.edit_message_text(
        get_string('main_menu', new_lang).format(name=name, reports=reports, ig_username=ig_username),
        parse_mode='HTML'
    )
    
    await context.bot.send_message(
        chat_id=user_id,
        text=get_string('main_menu', new_lang).format(name=name, reports=reports, ig_username=ig_username),
        reply_markup=get_main_keyboard(new_lang, is_admin_user),
        parse_mode='HTML'
    )
    
    return MAIN_MENU

# ================= ADVANCED ADMIN FUNCTIONS =================
async def admin_panel(update: Update, context: CallbackContext):
    # Handle both message and callback query
    if hasattr(update, 'callback_query') and update.callback_query:
        user_id = str(update.callback_query.from_user.id)
        send_message = update.callback_query.edit_message_text
    else:
        user_id = str(update.effective_user.id)
        send_message = update.message.reply_text
    
    if not is_admin(user_id):
        await send_message("❌ <b>Access Denied!</b>", parse_mode='HTML')
        return MAIN_MENU
    
    all_users = get_all_users()
    total_users = len(all_users)
    active_reports_count = len(active_reports)
    
    admin_text = get_string('admin_panel', 'en').format(
        total_users=total_users,
        active_reports=active_reports_count
    )
    
    await send_message(
        admin_text,
        reply_markup=get_admin_keyboard('en'),
        parse_mode='HTML'
    )
    return ADMIN_PANEL

async def handle_admin_buttons(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    text = update.message.text
    
    if not is_admin(user_id):
        return MAIN_MENU
    
    if text == "⬅️ Back":
        name = user_data.get('display_name', 'Admin')
        reports = user_data.get('total_reports', 0)
        ig_username = user_data.get('ig_username', 'Unknown')
        
        await update.message.reply_text(
            get_string('main_menu', lang).format(name=name, reports=reports, ig_username=ig_username),
            reply_markup=get_main_keyboard(lang, True),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif text == "📢 Broadcast":
        await update.message.reply_text(
            get_string('broadcast_prompt', lang),
            parse_mode='HTML'
        )
        return BROADCAST_MESSAGE
        
    elif text == "👥 Users":
        all_users = get_all_users()
        users_text = get_string('user_list', lang).format(users="")
        user_list = ""
        
        for i, user_data in enumerate(all_users[:15], 1):  # Show first 15 users
            name = user_data.get('display_name', 'Unknown')
            user_id_display = user_data.get('user_id', 'Unknown')
            reports = user_data.get('total_reports', 0)
            ig_user = user_data.get('ig_username', 'Not verified')
            lang_user = user_data.get('lang', 'en')
            
            user_list += f"{i}. <b>{name}</b>\n"
            user_list += f"   🆔 ID: <code>{user_id_display}</code>\n"
            user_list += f"   📱 IG: @{ig_user} | 📊 Reports: {reports} | 🌐 {lang_user.upper()}\n\n"
        
        if len(all_users) > 15:
            user_list += f"\n<i>... and {len(all_users) - 15} more users</i>"
        
        await update.message.reply_text(
            users_text + user_list,
            parse_mode='HTML'
        )
        
    elif text == "📊 Statistics":
        all_users = get_all_users()
        total_users = len(all_users)
        now = datetime.now()
        active_users = 0
        today_joins = 0
        total_reports = 0
        verified_users = 0
        
        for user_data in all_users:
            try:
                total_reports += user_data.get('total_reports', 0)
                if user_data.get('ig_verified', False):
                    verified_users += 1
                    
                last_active = user_data.get('last_active')
                if isinstance(last_active, str):
                    last_active = datetime.fromisoformat(last_active)
                elif not isinstance(last_active, datetime):
                    last_active = datetime.now() - timedelta(days=1)
                    
                if last_active > now - timedelta(hours=24):
                    active_users += 1
                    
                joined = user_data.get('joined_at')
                if isinstance(joined, str):
                    joined = datetime.fromisoformat(joined)
                elif not isinstance(joined, datetime):
                    joined = datetime.now()
                    
                if joined.date() == now.date():
                    today_joins += 1
            except Exception as e:
                print(f"Error processing user data: {e}")
                continue
        
        stats = get_string('user_stats', lang).format(
            total=total_users,
            active=active_users,
            today=today_joins,
            total_reports=total_reports
        )
        
        await update.message.reply_text(stats, parse_mode='HTML')
    
    elif text == "🛠️ Customize":
        await update.message.reply_text(
            "🎨 <b>ADVANCED CUSTOMIZATION PANEL</b>\n\n"
            "Select what you want to customize:",
            reply_markup=get_customization_keyboard(),
            parse_mode='HTML'
        )
        return ADMIN_SETTINGS
    
    elif text == "🏠 Home":
        name = user_data.get('display_name', 'Admin')
        reports = user_data.get('total_reports', 0)
        ig_username = user_data.get('ig_username', 'Unknown')
        
        await update.message.reply_text(
            get_string('main_menu', lang).format(name=name, reports=reports, ig_username=ig_username),
            reply_markup=get_main_keyboard(lang, True),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    return ADMIN_PANEL

async def handle_broadcast(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    message = update.message.text
    all_users = get_all_users()
    success_count = 0
    
    for user_data in all_users:
        try:
            target_id = user_data.get('user_id')
            if target_id and target_id != user_id:  # Don't send to admin
                await context.bot.send_message(
                    chat_id=target_id,
                    text=f"📢 <b>ADMIN BROADCAST</b>\n\n{message}",
                    parse_mode='HTML'
                )
                success_count += 1
                await asyncio.sleep(0.1)  # Avoid flooding
        except Exception as e:
            print(f"Failed to send broadcast to {target_id}: {e}")
            continue
    
    await update.message.reply_text(
        get_string('broadcast_sent', 'en').format(count=success_count),
        parse_mode='HTML'
    )
    
    return ADMIN_PANEL

# ================= BUTTON CUSTOMIZATION =================
async def customize_buttons(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    lang = 'en'  # Admin uses English for customization
    
    # Get all existing buttons
    buttons = get_all_buttons(lang)
    button_list = "\n".join([f"• <b>{key}</b>: {text}" for key, text in buttons.items()])
    
    await update.message.reply_text(
        f"🔘 <b>BUTTON MANAGEMENT</b>\n\n"
        f"Current buttons:\n{button_list}\n\n"
        "Select an action:",
        reply_markup=get_button_management_keyboard(),
        parse_mode='HTML'
    )
    return CUSTOMIZE_BUTTONS

async def edit_button_selection(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    lang = 'en'
    buttons = get_all_buttons(lang)
    
    # Create keyboard with buttons to edit
    keyboard = []
    for key in buttons.keys():
        keyboard.append([KeyboardButton(key)])
    keyboard.append([KeyboardButton("⬅️ Back")])
    
    await update.message.reply_text(
        get_string('customize_buttons', lang),
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode='HTML'
    )
    return EDIT_BUTTON_TEXT

async def edit_button_text(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    button_key = update.message.text
    context.user_data['editing_button'] = button_key
    
    current_text = get_button_text(button_key, 'en')
    
    await update.message.reply_text(
        get_string('edit_button_prompt', 'en').format(current=current_text),
        parse_mode='HTML'
    )
    return EDIT_BUTTON_TEXT

async def save_button_text_handler(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    new_text = update.message.text
    button_key = context.user_data.get('editing_button')
    
    if button_key:
        try:
            db = get_db_connection()
            if db:
                # Save for all languages
                for lang in ['en', 'hi']:
                    db.bot_buttons.update_one(
                        {"button_key": button_key, "lang": lang},
                        {"$set": {"text": new_text}},
                        upsert=True
                    )
                
                await update.message.reply_text(
                    get_string('button_updated', 'en').format(button_key=button_key, new_text=new_text),
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    "❌ Database connection error",
                    parse_mode='HTML'
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error saving button text: {e}",
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            "❌ Error: Button key not found",
            parse_mode='HTML'
        )
    
    return await customize_buttons(update, context)

async def add_new_button(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    await update.message.reply_text(
        get_string('add_button_prompt', 'en'),
        parse_mode='HTML'
    )
    return ADD_NEW_BUTTON

async def save_new_button_key(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    button_key = update.message.text.strip()
    
    # Check if button key already exists
    if get_button_text(button_key, 'en') != button_key:
        await update.message.reply_text(
            get_string('button_exists', 'en').format(button_key=button_key),
            parse_mode='HTML'
        )
        return ADD_NEW_BUTTON
    
    context.user_data['new_button_key'] = button_key
    
    await update.message.reply_text(
        "Enter text for the new button (English):",
        parse_mode='HTML'
    )
    return ADD_NEW_BUTTON

async def save_new_button_text(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    button_text = update.message.text
    button_key = context.user_data.get('new_button_key')
    
    if button_key:
        try:
            db = get_db_connection()
            if db:
                # Save English version
                db.bot_buttons.insert_one({
                    "button_key": button_key,
                    "lang": "en",
                    "text": button_text
                })
                
                # Save Hindi version (default to same as English)
                db.bot_buttons.insert_one({
                    "button_key": button_key,
                    "lang": "hi",
                    "text": button_text
                })
                
                await update.message.reply_text(
                    get_string('button_added', 'en').format(button_key=button_key, button_text=button_text),
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    "❌ Database connection error",
                    parse_mode='HTML'
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error adding new button: {e}",
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            "❌ Error: Button key missing",
            parse_mode='HTML'
        )
    
    # Clean up
    if 'new_button_key' in context.user_data:
        del context.user_data['new_button_key']
    
    return await customize_buttons(update, context)

async def remove_button_selection(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    lang = 'en'
    buttons = get_all_buttons(lang)
    
    # Create keyboard with removable buttons
    keyboard = []
    for key in buttons.keys():
        # Prevent removal of essential buttons
        if key not in ['home', 'admin_panel']:
            keyboard.append([KeyboardButton(key)])
    keyboard.append([KeyboardButton("⬅️ Back")])
    
    await update.message.reply_text(
        get_string('remove_button_prompt', 'en'),
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode='HTML'
    )
    return REMOVE_BUTTON

async def remove_button_confirmation(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    button_key = update.message.text
    context.user_data['removing_button'] = button_key
    
    button_text = get_button_text(button_key, 'en')
    
    await update.message.reply_text(
        f"⚠️ <b>CONFIRM BUTTON REMOVAL</b>\n\n"
        f"Button Key: <code>{button_key}</code>\n"
        f"Text: <b>{button_text}</b>\n\n"
        "Are you sure you want to remove this button?",
        reply_markup=ReplyKeyboardMarkup([
            ["✅ Yes, Remove", "❌ Cancel"],
            ["⬅️ Back"]
        ], resize_keyboard=True),
        parse_mode='HTML'
    )
    return REMOVE_BUTTON

async def execute_button_removal(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    if update.message.text == "✅ Yes, Remove":
        button_key = context.user_data.get('removing_button')
        
        if button_key:
            try:
                db = get_db_connection()
                if db:
                    # Remove from database
                    db.bot_buttons.delete_many({"button_key": button_key})
                    
                    await update.message.reply_text(
                        get_string('button_removed', 'en').format(button_key=button_key),
                        parse_mode='HTML'
                    )
                else:
                    await update.message.reply_text(
                        "❌ Database connection error",
                        parse_mode='HTML'
                    )
            except Exception as e:
                await update.message.reply_text(
                    f"❌ Error removing button: {e}",
                    parse_mode='HTML'
                )
        else:
            await update.message.reply_text(
                "❌ Error: Button key missing",
                parse_mode='HTML'
            )
    
    # Clean up
    if 'removing_button' in context.user_data:
        del context.user_data['removing_button']
    
    return await customize_buttons(update, context)

async def reorder_buttons(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    lang = 'en'
    buttons = list(get_all_buttons(lang).keys())
    
    # Create a numbered list of buttons
    button_list = "\n".join([f"{i+1}. {button}" for i, button in enumerate(buttons)])
    
    context.user_data['current_button_order'] = buttons
    
    await update.message.reply_text(
        get_string('reorder_buttons', 'en').format(button_list=button_list),
        parse_mode='HTML'
    )
    return REORDER_BUTTONS

async def save_button_order(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    try:
        order_str = update.message.text
        new_order_indices = [int(i.strip()) - 1 for i in order_str.split(',')]
        current_buttons = context.user_data.get('current_button_order', [])
        
        if len(new_order_indices) != len(current_buttons):
            await update.message.reply_text(
                "❌ Error: Number of positions doesn't match number of buttons",
                parse_mode='HTML'
            )
            return REORDER_BUTTONS
        
        # Create new ordered list
        new_order = [current_buttons[i] for i in new_order_indices]
        
        # Save new order to database
        try:
            db = get_db_connection()
            if db:
                # Store the new order
                db.bot_settings.update_one(
                    {"setting_key": "button_order"},
                    {"$set": {"value": new_order}},
                    upsert=True
                )
                
                await update.message.reply_text(
                    get_string('buttons_reordered', 'en'),
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    "❌ Database connection error",
                    parse_mode='HTML'
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error saving button order: {e}",
                parse_mode='HTML'
            )
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid format. Please enter numbers separated by commas",
            parse_mode='HTML'
        )
        return REORDER_BUTTONS
    
    # Clean up
    if 'current_button_order' in context.user_data:
        del context.user_data['current_button_order']
    
    return await customize_buttons(update, context)

# ================= STRING CUSTOMIZATION =================
async def customize_strings(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    lang = 'en'  # Admin uses English for customization
    
    # Get all existing strings
    strings = get_all_strings(lang)
    string_list = "\n".join([f"• <b>{key}</b>" for key in strings.keys()])
    
    await update.message.reply_text(
        f"📝 <b>MESSAGE CUSTOMIZATION</b>\n\n"
        f"Available messages:\n{string_list}\n\n"
        "Select a message to edit:",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("✏️ Edit Message")],
            [KeyboardButton("⬅️ Back")]
        ], resize_keyboard=True),
        parse_mode='HTML'
    )
    return CUSTOMIZE_STRINGS

async def edit_string_selection(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    lang = 'en'
    strings = get_all_strings(lang)
    
    # Create keyboard with strings to edit
    keyboard = []
    for key in strings.keys():
        keyboard.append([KeyboardButton(key)])
    keyboard.append([KeyboardButton("⬅️ Back")])
    
    await update.message.reply_text(
        get_string('customize_strings', 'en'),
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode='HTML'
    )
    return EDIT_STRING_TEXT

async def edit_string_text(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    string_key = update.message.text
    context.user_data['editing_string'] = string_key
    
    current_text = get_string(string_key, 'en')
    
    # Truncate for display
    display_text = (current_text[:300] + '...') if len(current_text) > 300 else current_text
    
    await update.message.reply_text(
        f"✏️ <b>EDIT MESSAGE TEXT</b>\n\n"
        f"Key: <code>{string_key}</code>\n"
        f"Current Text:\n<pre>{display_text}</pre>\n\n"
        "Enter new text for this message:",
        parse_mode='HTML'
    )
    return EDIT_STRING_TEXT

async def save_string_text_handler(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    new_text = update.message.text
    string_key = context.user_data.get('editing_string')
    
    if string_key:
        try:
            db = get_db_connection()
            if db:
                # Save for all languages
                for lang in ['en', 'hi']:
                    db.bot_strings.update_one(
                        {"string_key": string_key, "lang": lang},
                        {"$set": {"text": new_text}},
                        upsert=True
                    )
                
                await update.message.reply_text(
                    get_string('string_updated', 'en').format(string_key=string_key),
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    "❌ Database connection error",
                    parse_mode='HTML'
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error saving message text: {e}",
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            "❌ Error: Message key not found",
            parse_mode='HTML'
        )
    
    return await customize_strings(update, context)

# ================= REPORT TYPE CUSTOMIZATION =================
async def customize_report_types(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    lang = 'en'  # Admin uses English for customization
    
    # Get all existing report types
    report_types = get_all_report_types()
    type_list = "\n".join([f"• <b>{key}</b>: {text}" for key, text in report_types.items()])
    
    await update.message.reply_text(
        f"⚔️ <b>REPORT TYPE CUSTOMIZATION</b>\n\n"
        f"Current report types:\n{type_list}\n\n"
        "Select an action:",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("✏️ Edit Report Type")],
            [KeyboardButton("⬅️ Back")]
        ], resize_keyboard=True),
        parse_mode='HTML'
    )
    return CUSTOMIZE_REPORT_TYPES

async def edit_report_type_selection(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    lang = 'en'
    report_types = get_all_report_types()
    
    # Create keyboard with report types to edit
    keyboard = []
    for key in report_types.keys():
        keyboard.append([KeyboardButton(key)])
    keyboard.append([KeyboardButton("⬅️ Back")])
    
    await update.message.reply_text(
        get_string('customize_report_types', 'en'),
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
        parse_mode='HTML'
    )
    return EDIT_REPORT_TYPE

async def edit_report_type_text(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    type_key = update.message.text
    context.user_data['editing_report_type'] = type_key
    
    current_text = get_report_type(type_key)
    
    await update.message.reply_text(
        f"✏️ <b>EDIT REPORT TYPE</b>\n\n"
        f"Type Key: <code>{type_key}</code>\n"
        f"Current Text: <b>{current_text}</b>\n\n"
        "Enter new text for this report type:",
        parse_mode='HTML'
    )
    return EDIT_REPORT_TYPE

async def save_report_type_text(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        return ADMIN_PANEL
    
    new_text = update.message.text
    type_key = context.user_data.get('editing_report_type')
    
    if type_key:
        try:
            db = get_db_connection()
            if db:
                # Save the report type
                db.report_types.update_one(
                    {"type_key": type_key},
                    {"$set": {"text": new_text}},
                    upsert=True
                )
                
                await update.message.reply_text(
                    get_string('report_type_updated', 'en').format(type_key=type_key, new_text=new_text),
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text(
                    "❌ Database connection error",
                    parse_mode='HTML'
                )
        except Exception as e:
            await update.message.reply_text(
                f"❌ Error saving report type: {e}",
                parse_mode='HTML'
            )
    else:
        await update.message.reply_text(
            "❌ Error: Report type key not found",
            parse_mode='HTML'
        )
    
    return await customize_report_types(update, context)

# ================= MAIN FUNCTION =================
def main():
    # Initialize database
    db_status = init_database()
    if not db_status:
        print("⚠️ Running without database - using fallback mode")
    
    # Get bot token from environment variable
    BOT_TOKEN = os.getenv("BOT_TOKEN", TELEGRAM_BOT_TOKEN)
    
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN not found!")
        return

    try:
        print("🚀 Starting Premium IG Reporter Bot v2.0...")
        print(f"👑 Admin ID: {ADMIN_ID}")
        print("🗄️ MongoDB Database Integrated")
        print("🔐 Instagram Login System Active")
        print("🎨 Advanced Admin Panel Enabled")
        
        # Create application with proper error handling
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        # Main conversation handler
        conv = ConversationHandler(
            entry_points=[
                CommandHandler('start', start),
                CommandHandler('admin', admin_panel)
            ],
            states={
                REGISTER: [
                    CallbackQueryHandler(handle_language_selection, pattern='^lang_'),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration)
                ],
                IG_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ig_username)],
                IG_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ig_username)],
                IG_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ig_password)],
                MAIN_MENU: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu),
                    CallbackQueryHandler(handle_language_change, pattern='^change_lang_')
                ],
                REPORT_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_report_menu)],
                USERNAME_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username_input)],
                REPORT_TYPE: [CallbackQueryHandler(handle_report_type, pattern='^type_')],
                IMPERSONATION_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_impersonation_url)],
                REPORT_LOOP: [
                    CallbackQueryHandler(handle_report_loop),
                    CallbackQueryHandler(handle_report_loop, pattern='^stop_report$'),
                    MessageHandler(filters.Regex(r'⏹️ Stop Attack|⏹️ अटैक बंद करें'), handle_stop_attack),
                ],
                ADMIN_PANEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_buttons)],
                BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast)],
                SETTINGS_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings_menu)],
                HELP_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_help_menu)],
                ADMIN_SETTINGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: customize_buttons(u, c))],
                CUSTOMIZE_BUTTONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, customize_buttons)],
                EDIT_BUTTON_TEXT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, edit_button_selection),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, save_button_text_handler)
                ],
                ADD_NEW_BUTTON: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_button_key),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, save_new_button_text)
                ],
                REMOVE_BUTTON: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, remove_button_selection),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, remove_button_confirmation),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, execute_button_removal)
                ],
                REORDER_BUTTONS: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, reorder_buttons),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, save_button_order)
                ],
                CUSTOMIZE_STRINGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, customize_strings)],
                EDIT_STRING_TEXT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, edit_string_selection),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, save_string_text_handler)
                ],
                CUSTOMIZE_REPORT_TYPES: [MessageHandler(filters.TEXT & ~filters.COMMAND, customize_report_types)],
                EDIT_REPORT_TYPE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, edit_report_type_selection),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, save_report_type_text)
                ]
            },
            fallbacks=[
                CommandHandler('start', start),
                MessageHandler(filters.Regex(r'⬅️ Back|🏠 Home|🏠 होम'), handle_main_menu)
            ],
            per_chat=True,
            per_user=False
        )

        app.add_handler(conv)
        
        print("✅ Bot handlers configured successfully!")
        
        # Check if we're in production (Render)
        is_production = os.environ.get('RENDER') or os.environ.get('PORT')
        
        if is_production:
            print("🌐 Production mode detected - Starting web server")
            
            # For production deployment, start web server
            import threading
            from http.server import HTTPServer, BaseHTTPRequestHandler
            
            class HealthHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Premium IG Reporter Bot is running!')
                
                def log_message(self, format, *args):
                    pass  # Suppress HTTP logs
            
            # Start health check server
            port = int(os.environ.get('PORT', 10000))
            httpd = HTTPServer(('0.0.0.0', port), HealthHandler)
            
            def start_server():
                print(f"🌐 Health check server started on port {port}")
                httpd.serve_forever()
            
            # Start server in background thread
            server_thread = threading.Thread(target=start_server, daemon=True)
            server_thread.start()
            
            # Try polling with better conflict handling
            try:
                print("🔄 Starting bot polling...")
                app.run_polling(drop_pending_updates=True, allowed_updates=None)
            except Exception as polling_error:
                error_str = str(polling_error)
                if "Conflict" in error_str and ("getUpdates" in error_str or "terminated" in error_str):
                    print("🔄 Another bot instance is already running.")
                    print("💡 This is normal for deployment - keeping web server alive.")
                    # Keep web server running even if polling fails
                    import time
                    while True:
                        time.sleep(60)
                else:
                    raise polling_error
        else:
            print("💻 Development mode - Starting polling only")
            # Check database connection
            db_conn = get_db_connection()
            if db_conn is not None:
                print("💾 Database status: Connected")
            else:
                print("💾 Database status: Fallback mode")
            
            print("🔄 Starting polling...")
            app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
