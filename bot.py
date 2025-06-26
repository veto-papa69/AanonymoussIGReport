
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

# Constants
ADMIN_ID = 6881713177

# States for ConversationHandler
MAIN_MENU, REGISTER, PROFILE, REPORT_MENU, USERNAME_INPUT, REPORT_TYPE, IMPERSONATION_URL, REPORT_LOOP = range(8)

# Admin Panel States
ADMIN_PANEL, BROADCAST_MESSAGE, VIEW_USERS, USER_STATS, ADMIN_SETTINGS, EDIT_MESSAGES, CUSTOMIZE_BUTTONS, EDIT_BUTTON_TEXT = range(100, 108)

# Customizable settings (admin can modify these)
BOT_SETTINGS = {
    'font_style': 'HTML',  # HTML, Markdown, Plain
    'theme': 'premium',    # premium, minimal, classic
    'emoji_style': 'full', # full, minimal, none
    'button_style': 'modern' # modern, classic, minimal
}

# Language strings with customizable elements
STRINGS = {
    'en': {
        'welcome': "🔥 <b>PREMIUM IG REPORTER V2.0</b> 🔥\n\n🎯 <b>Ultimate Instagram Mass Reporter</b>\n⚡ Lightning Fast • 🔒 100% Anonymous • 💯 Guaranteed Results\n\n🚀 <i>Join thousands of satisfied users!</i>",
        'register_prompt': "🎭 <b>NEW USER REGISTRATION</b>\n\n📝 Enter your <b>Display Name</b>:\n<i>This will be shown in your profile</i>",
        'registration_success': "🎉 <b>REGISTRATION SUCCESSFUL!</b>\n\n✅ Welcome aboard, <b>{name}</b>!\n🚀 Access to all premium features unlocked!",
        'main_menu': "🏠 <b>MAIN DASHBOARD</b>\n\n👋 Hello, <b>{name}</b>!\n📊 Total Reports: <b>{reports}</b>\n🎯 Choose your action:",
        'profile': "👤 <b>USER PROFILE</b>\n\n📝 Name: <b>{name}</b>\n📅 Member Since: <b>{date}</b>\n📊 Total Reports: <b>{reports}</b>\n⚡ Status: <b>PREMIUM</b>\n🔥 Rank: <b>ELITE REPORTER</b>\n\n📈 <b>Report History:</b>\n{report_history}",
        'report_menu': "⚔️ <b>REPORT ATTACK CENTER</b>\n\n🎯 Ready to launch mass reports?",
        'send_username': "📱 <b>TARGET SELECTION</b>\n\n🎯 Enter Instagram username to attack:\n\n⚠️ <b>Format:</b> @username\n❌ <b>No emojis allowed</b>\n\n<i>Example: @target_account</i>",
        'choose_report_type': "⚔️ <b>SELECT WEAPON TYPE</b>\n\n🎯 Choose violation category for maximum impact:",
        'ask_impersonation_url': "🔗 <b>IMPERSONATION EVIDENCE</b>\n\n📎 Send URL of the original account being impersonated:\n<i>This increases report success rate</i>",
        'confirm_start': "🚀 <b>ATTACK READY TO LAUNCH</b>\n\n🎯 Target: <b>@{username}</b>\n⚔️ Weapon: <b>{type}</b>\n💥 Mode: <b>INFINITE ASSAULT</b>\n\n✅ Press LAUNCH to begin destruction!",
        'reporting_started': "💥 <b>MASS ATTACK INITIATED!</b>\n\n🎯 Target: <b>@{username}</b>\n🔥 Status: <b>BOMBING IN PROGRESS</b>\n⚡ Reports launching every 1-3 seconds...",
        'reporting_stopped': "⏹️ <b>ATTACK TERMINATED</b>\n\n📊 Mission completed by operator\n🎯 Target received multiple violations\n💥 Total strikes: <b>{total_strikes}</b>",
        'report_success': "✅ <b>STRIKE #{count} SUCCESSFUL</b>\n🎯 Target: <b>@{username}</b>\n💥 Status: <b>DIRECT HIT</b>\n⚡ Damage: <b>CRITICAL</b>",
        'report_failed': "❌ <b>STRIKE #{count} BLOCKED</b>\n🎯 Target: <b>@{username}</b>\n⚠️ Status: <b>RETRYING</b>\n🔄 Adjusting strategy...",
        'invalid_username': "❌ <b>INVALID TARGET FORMAT</b>\n\n⚠️ Username must:\n• Start with @\n• No emojis allowed\n• Only letters, numbers, dots, underscores\n\n<i>Try again with correct format</i>",
        'admin_panel': "👑 <b>ADMIN CONTROL CENTER</b>\n\n🛠️ Master Administrator Dashboard\n🎛️ Full bot control access",
        'user_stats': "📊 <b>BOT ANALYTICS</b>\n\n👥 Total Users: <b>{total}</b>\n⚡ Active (24h): <b>{active}</b>\n📅 New Today: <b>{today}</b>\n📈 Total Reports: <b>{total_reports}</b>",
        'user_list': "👥 <b>REGISTERED USERS</b>\n\n{users}",
        'broadcast_prompt': "📢 <b>BROADCAST MESSAGE</b>\n\nType message to send to all users:",
        'broadcast_sent': "✅ <b>Broadcast sent to {count} users!</b>",
        'my_reports': "📊 <b>MY REPORT HISTORY</b>\n\n{report_list}",
        'no_reports': "📭 <b>No reports found</b>\n\nStart reporting to see your history here!",
        'customize_buttons': "🎨 <b>CUSTOMIZE BUTTONS</b>\n\nSelect button to edit:",
        'edit_button_prompt': "✏️ <b>EDIT BUTTON TEXT</b>\n\nCurrent: <b>{current}</b>\n\nEnter new text:"
    },
    'hi': {
        'welcome': "🔥 <b>प्रीमियम IG रिपोर्टर V2.0</b> 🔥\n\n🎯 <b>अल्टीमेट इंस्टाग्राम मास रिपोर्टर</b>\n⚡ बिजली तेज़ • 🔒 100% गुमनाम • 💯 गारंटीड रिजल्ट\n\n🚀 <i>हजारों संतुष्ट यूजर्स के साथ जुड़ें!</i>",
        'register_prompt': "🎭 <b>नया यूजर रजिस्ट्रेशन</b>\n\n📝 अपना <b>नाम</b> दर्ज करें:\n<i>यह आपकी प्रोफाइल में दिखेगा</i>",
        'registration_success': "🎉 <b>रजिस्ट्रेशन सफल!</b>\n\n✅ स्वागत है, <b>{name}</b>!\n🚀 सभी प्रीमियम फीचर्स अनलॉक!",
        'main_menu': "🏠 <b>मुख्य डैशबोर्ड</b>\n\n👋 नमस्ते, <b>{name}</b>!\n📊 कुल रिपोर्ट्स: <b>{reports}</b>\n🎯 अपनी कार्रवाई चुनें:",
        'profile': "👤 <b>यूजर प्रोफाइल</b>\n\n📝 नाम: <b>{name}</b>\n📅 सदस्य: <b>{date}</b>\n📊 कुल रिपोर्ट्स: <b>{reports}</b>\n⚡ स्थिति: <b>प्रीमियम</b>\n🔥 रैंक: <b>एलीट रिपोर्टर</b>\n\n📈 <b>रिपोर्ट हिस्ट्री:</b>\n{report_history}",
        'report_menu': "⚔️ <b>रिपोर्ट अटैक सेंटर</b>\n\n🎯 मास रिपोर्ट्स लॉन्च करने के लिए तैयार?",
        'send_username': "📱 <b>टारगेट सिलेक्शन</b>\n\n🎯 अटैक करने के लिए Instagram username दर्ज करें:\n\n⚠️ <b>फॉर्मेट:</b> @username\n❌ <b>कोई इमोजी अलाउड नहीं</b>\n\n<i>उदाहरण: @target_account</i>",
        'choose_report_type': "⚔️ <b>हथियार का प्रकार चुनें</b>\n\n🎯 अधिकतम प्रभाव के लिए उल्लंघन श्रेणी चुनें:",
        'ask_impersonation_url': "🔗 <b>नकल का सबूत</b>\n\n📎 मूल अकाउंट का URL भेजें जिसकी नकल की जा रही है:\n<i>यह रिपोर्ट सफलता दर बढ़ाता है</i>",
        'confirm_start': "🚀 <b>अटैक लॉन्च के लिए तैयार</b>\n\n🎯 टारगेट: <b>@{username}</b>\n⚔️ हथियार: <b>{type}</b>\n💥 मोड: <b>अनंत हमला</b>\n\n✅ विनाश शुरू करने के लिए LAUNCH दबाएं!",
        'reporting_started': "💥 <b>मास अटैक शुरू!</b>\n\n🎯 टारगेट: <b>@{username}</b>\n🔥 स्थिति: <b>बमबारी जारी</b>\n⚡ हर 1-3 सेकंड में रिपोर्ट्स...",
        'reporting_stopped': "⏹️ <b>अटैक समाप्त</b>\n\n📊 ऑपरेटर द्वारा मिशन पूरा\n🎯 टारगेट को कई उल्लंघन मिले\n💥 कुल स्ट्राइक्स: <b>{total_strikes}</b>",
        'report_success': "✅ <b>स्ट्राइक #{count} सफल</b>\n🎯 टारगेट: <b>@{username}</b>\n💥 स्थिति: <b>डायरेक्ट हिट</b>\n⚡ नुकसान: <b>गंभीर</b>",
        'report_failed': "❌ <b>स्ट्राइक #{count} ब्लॉक</b>\n🎯 टारगेट: <b>@{username}</b>\n⚠️ स्थिति: <b>पुनः प्रयास</b>\n🔄 रणनीति बदल रहे हैं...",
        'invalid_username': "❌ <b>गलत टारगेट फॉर्मेट</b>\n\n⚠️ Username में होना चाहिए:\n• @ से शुरुआत\n• कोई इमोजी नहीं\n• केवल अक्षर, संख्या, डॉट, अंडरस्कोर\n\n<i>सही फॉर्मेट के साथ फिर कोशिश करें</i>",
        'admin_panel': "👑 <b>एडमिन कंट्रोल सेंटर</b>\n\n🛠️ मास्टर एडमिनिस्ट्रेटर डैशबोर्ड\n🎛️ पूर्ण बॉट नियंत्रण एक्सेस",
        'user_stats': "📊 <b>बॉट एनालिटिक्स</b>\n\n👥 कुल यूजर्स: <b>{total}</b>\n⚡ सक्रिय (24घं): <b>{active}</b>\n📅 आज नए: <b>{today}</b>\n📈 कुल रिपोर्ट्स: <b>{total_reports}</b>",
        'user_list': "👥 <b>रजिस्टर्ड यूजर्स</b>\n\n{users}",
        'broadcast_prompt': "📢 <b>ब्रॉडकास्ट मैसेज</b>\n\nसभी यूजर्स को भेजने के लिए मैसेज टाइप करें:",
        'broadcast_sent': "✅ <b>ब्रॉडकास्ट {count} यूजर्स को भेजा गया!</b>",
        'my_reports': "📊 <b>मेरी रिपोर्ट हिस्ट्री</b>\n\n{report_list}",
        'no_reports': "📭 <b>कोई रिपोर्ट नहीं मिली</b>\n\nअपनी हिस्ट्री यहाँ देखने के लिए रिपोर्टिंग शुरू करें!",
        'customize_buttons': "🎨 <b>बटन कस्टमाइज़ करें</b>\n\nएडिट करने के लिए बटन चुनें:",
        'edit_button_prompt': "✏️ <b>बटन टेक्स्ट एडिट करें</b>\n\nमौजूदा: <b>{current}</b>\n\nनया टेक्स्ट दर्ज करें:"
    }
}

# Customizable button texts
BUTTON_TEXTS = {
    'en': {
        'report_attack': '⚔️ Report Attack',
        'profile': '👤 Profile',
        'my_reports': '📊 My Reports',
        'home': '🏠 Home',
        'admin_panel': '👑 Admin Panel',
        'language': '🌐 Language',
        'help': 'ℹ️ Help',
        'settings': '⚙️ Settings'
    },
    'hi': {
        'report_attack': '⚔️ रिपोर्ट अटैक',
        'profile': '👤 प्रोफाइल',
        'my_reports': '📊 मेरी रिपोर्ट्स',
        'home': '🏠 होम',
        'admin_panel': '👑 एडमिन पैनल',
        'language': '🌐 भाषा बदलें',
        'help': 'ℹ️ सहायता',
        'settings': '⚙️ सेटिंग्स'
    }
}

# Report types with enhanced emojis
REPORT_TYPES = {
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
            db.bot_settings.create_index("setting_key", unique=True, sparse=True)
        except Exception as index_error:
            print(f"⚠️ Index warning: {index_error}")
        
        print("✅ MongoDB collections and indexes initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

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
    buttons = BUTTON_TEXTS[lang]
    
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
            [KeyboardButton(buttons['language']), KeyboardButton(buttons['help'])]
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
        
        welcome_text = STRINGS['en']['welcome']
        if is_admin_user:
            welcome_text += "\n\n👑 <b>ADMIN ACCESS DETECTED</b>"
        
        await update.message.reply_text(
            welcome_text + '\n\n🌐 <b>Choose Language / भाषा चुनें:</b>',
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return REGISTER
    else:
        # Update last active
        user_data['last_active'] = now
        save_user(user_id, user_data)
        
        lang = user_data.get('lang', 'en')
        name = user_data.get('display_name', 'User')
        reports = user_data.get('total_reports', 0)
        
        await update.message.reply_text(
            STRINGS[lang]['main_menu'].format(name=name, reports=reports),
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
        STRINGS[lang]['register_prompt'],
        parse_mode='HTML'
    )
    return REGISTER

async def handle_registration(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    display_name = update.message.text.strip()
    lang = context.user_data.get('lang', 'en')
    now = datetime.now()
    is_admin_user = is_admin(user_id)
    
    # Save user data to database
    user_data = {
        "username": update.effective_user.username or "Unknown",
        "display_name": display_name,
        "lang": lang,
        "joined_at": now,
        "last_active": now,
        "total_reports": 0,
        "successful_reports": 0,
        "failed_reports": 0,
        "is_admin": is_admin_user
    }
    
    save_user(user_id, user_data)
    
    await update.message.reply_text(
        STRINGS[lang]['registration_success'].format(name=display_name),
        parse_mode='HTML'
    )
    
    await asyncio.sleep(2)
    
    await update.message.reply_text(
        STRINGS[lang]['main_menu'].format(name=display_name, reports=0),
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
    is_admin_user = is_admin(user_id)
    text = update.message.text
    buttons = BUTTON_TEXTS[lang]
    
    if text == buttons['report_attack']:
        await update.message.reply_text(
            STRINGS[lang]['report_menu'],
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🚀 LAUNCH ATTACK / अटैक शुरू करें", callback_data="new_report")
            ]]),
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
            STRINGS[lang]['profile'].format(name=name, date=join_date, reports=reports, report_history=report_history),
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
                report_list += f"   📊 {success}/{total} success | 🎯 {REPORT_TYPES.get(report_type, report_type)}\n"
                report_list += f"   📅 {date}\n\n"
                
            await update.message.reply_text(
                STRINGS[lang]['my_reports'].format(report_list=report_list),
                parse_mode='HTML'
            )
        else:
            await update.message.reply_text(
                STRINGS[lang]['no_reports'],
                parse_mode='HTML'
            )
        return MAIN_MENU
        
    elif text == buttons['home']:
        await update.message.reply_text(
            STRINGS[lang]['main_menu'].format(name=name, reports=reports),
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
    
    return MAIN_MENU

async def handle_report_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    
    if query.data == "new_report":
        await query.edit_message_text(
            STRINGS[lang]['send_username'],
            parse_mode='HTML'
        )
        return USERNAME_INPUT

async def handle_username_input(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
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
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
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
            [InlineKeyboardButton("🚀 LAUNCH ATTACK", callback_data='start_report')],
            [InlineKeyboardButton("❌ ABORT MISSION", callback_data='cancel_report')]
        ]
        
        await query.edit_message_text(
            STRINGS[lang]['confirm_start'].format(username=username, type=type_name),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return REPORT_LOOP

async def handle_impersonation_url(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    
    context.user_data['impersonation_url'] = update.message.text
    username = context.user_data['target_username']
    
    keyboard = [
        [InlineKeyboardButton("🚀 LAUNCH ATTACK", callback_data='start_report')],
        [InlineKeyboardButton("❌ ABORT MISSION", callback_data='cancel_report')]
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
    user_data = get_user(user_id) or {}
    lang = user_data.get('lang', 'en')
    name = user_data.get('display_name', 'User')
    reports = user_data.get('total_reports', 0)
    is_admin_user = is_admin(user_id)
    username = context.user_data.get('target_username', '')
    report_type = context.user_data.get('report_type', 'spam')
    
    if query.data == 'start_report':
        # Start infinite reporting
        active_reports[user_id] = True
        
        # Start new report session
        session_id = start_report_session(user_id, username, report_type)
        context.user_data['session_id'] = session_id
        context.user_data['strike_count'] = 0
        
        keyboard = [[InlineKeyboardButton("⏹️ STOP ATTACK / अटैक बंद करें", callback_data='stop_report')]]
        
        await query.edit_message_text(
            STRINGS[lang]['reporting_started'].format(username=username),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        # Start the infinite reporting loop
        await start_infinite_reporting(context, user_id, username, report_type, lang, session_id)
        
    elif query.data == 'stop_report':
        active_reports[user_id] = False
        session_id = context.user_data.get('session_id')
        total_strikes = context.user_data.get('strike_count', 0)
        
        if session_id:
            end_report_session(session_id)
        
        try:
            await query.edit_message_text(
                STRINGS[lang]['reporting_stopped'].format(total_strikes=total_strikes),
                parse_mode='HTML'
            )
        except Exception as e:
            # Handle case where message can't be edited
            await context.bot.send_message(
                chat_id=user_id,
                text=STRINGS[lang]['reporting_stopped'].format(total_strikes=total_strikes),
                parse_mode='HTML'
            )
        
        await asyncio.sleep(2)
        
        # Return to main menu
        user_data = get_user(user_id) or {}
        updated_reports = user_data.get('total_reports', 0)
        
        await context.bot.send_message(
            chat_id=user_id,
            text=STRINGS[lang]['main_menu'].format(name=name, reports=updated_reports),
            reply_markup=get_main_keyboard(lang, is_admin_user),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif query.data == 'cancel_report':
        try:
            await query.edit_message_text(
                STRINGS[lang]['main_menu'].format(name=name, reports=reports),
                parse_mode='HTML'
            )
        except Exception as e:
            pass
        
        await context.bot.send_message(
            chat_id=user_id,
            text=STRINGS[lang]['main_menu'].format(name=name, reports=reports),
            reply_markup=get_main_keyboard(lang, is_admin_user),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    return REPORT_LOOP

async def start_infinite_reporting(context: CallbackContext, user_id: str, username: str, report_type: str, lang: str, session_id: int):
    report_count = 0
    last_message_id = None
    
    while active_reports.get(user_id, False):
        try:
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
                message = STRINGS[lang]['report_success'].format(count=report_count, username=username)
                # Update user report count on success
                update_user_reports(user_id, True)
            else:
                message = STRINGS[lang]['report_failed'].format(count=report_count, username=username)
                update_user_reports(user_id, False)
            
            # Send report status with stop button (only every 5 reports to avoid spam)
            if report_count % 5 == 1 or report_count <= 3:
                keyboard = [[InlineKeyboardButton("⏹️ STOP ATTACK / अटैक बंद करें", callback_data='stop_report')]]
                
                sent_message = await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                last_message_id = sent_message.message_id
            else:
                # Just send status without button to reduce button conflicts
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML'
                )
            
            # Random delay between 1-3 seconds
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
        except Exception as e:
            print(f"Error in reporting loop: {e}")
            active_reports[user_id] = False
            break

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
    
    await query.edit_message_text(
        STRINGS[new_lang]['main_menu'].format(name=name, reports=reports),
        parse_mode='HTML'
    )
    
    await context.bot.send_message(
        chat_id=user_id,
        text=STRINGS[new_lang]['main_menu'].format(name=name, reports=reports),
        reply_markup=get_main_keyboard(new_lang, is_admin_user),
        parse_mode='HTML'
    )
    
    return MAIN_MENU

# Admin functions with proper error handling
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
    now = datetime.now()
    active_users = 0
    today_joins = 0
    total_reports = 0
    
    for user_data in all_users:
        try:
            total_reports += user_data.get('total_reports', 0)
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
    
    stats = STRINGS['en']['user_stats'].format(
        total=total_users, 
        active=active_users, 
        today=today_joins,
        total_reports=total_reports
    )
    
    keyboard = [
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👥 View All Users", callback_data="admin_users")],
        [InlineKeyboardButton("🎨 Customize Bot", callback_data="admin_customize")],
        [InlineKeyboardButton("📊 Detailed Reports", callback_data="admin_detailed_reports")],
        [InlineKeyboardButton("⚙️ Bot Settings", callback_data="admin_settings")],
        [InlineKeyboardButton("🔄 Refresh Stats", callback_data="admin_refresh")]
    ]
    
    await send_message(
        STRINGS['en']['admin_panel'] + "\n\n" + stats,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return ADMIN_PANEL

async def handle_admin_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    if not is_admin(user_id):
        await query.edit_message_text("❌ <b>Access Denied!</b>", parse_mode='HTML')
        return MAIN_MENU
    
    if query.data == "admin_users":
        all_users = get_all_users()
        users_text = STRINGS['en']['user_list'].format(users="")
        user_list = ""
        
        for i, user_data in enumerate(all_users[:20], 1):  # Show first 20 users
            name = user_data.get('display_name', 'Unknown')
            user_id_display = user_data.get('user_id', 'Unknown')
            reports = user_data.get('total_reports', 0)
            success_reports = user_data.get('successful_reports', 0)
            lang = user_data.get('lang', 'en')
            status = "👑 Admin" if user_data.get('is_admin', False) else "👤 User"
            
            user_list += f"{i}. <b>{name}</b> {status}\n"
            user_list += f"   🆔 ID: <code>{user_id_display}</code>\n"
            user_list += f"   📊 Reports: {success_reports}/{reports} | 🌐 {lang.upper()}\n\n"
        
        if len(all_users) > 20:
            user_list += f"\n<i>... और {len(all_users) - 20} यूजर्स हैं</i>"
        
        # Add back button
        back_keyboard = [[InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_refresh")]]
        
        await query.edit_message_text(
            users_text + user_list,
            reply_markup=InlineKeyboardMarkup(back_keyboard),
            parse_mode='HTML'
        )
    
    elif query.data == "admin_broadcast":
        await query.edit_message_text(
            STRINGS['en']['broadcast_prompt'],
            parse_mode='HTML'
        )
        return BROADCAST_MESSAGE
    
    elif query.data == "admin_customize":
        keyboard = [
            [InlineKeyboardButton("🎨 Customize Buttons", callback_data="customize_buttons")],
            [InlineKeyboardButton("🎭 Change Theme", callback_data="change_theme")],
            [InlineKeyboardButton("📝 Edit Messages", callback_data="edit_messages")],
            [InlineKeyboardButton("🔤 Font Settings", callback_data="font_settings")],
            [InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_refresh")]
        ]
        
        await query.edit_message_text(
            "🎨 <b>BOT CUSTOMIZATION CENTER</b>\n\nSelect what you want to customize:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    elif query.data == "customize_buttons":
        keyboard = []
        for key, value in BUTTON_TEXTS['en'].items():
            keyboard.append([InlineKeyboardButton(f"✏️ {value}", callback_data=f"edit_btn_{key}")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_customize")])
        
        await query.edit_message_text(
            STRINGS['en']['customize_buttons'],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return CUSTOMIZE_BUTTONS
    
    elif query.data == "admin_refresh":
        # Create a fake update object for admin panel
        class FakeUpdate:
            def __init__(self, callback_query):
                self.callback_query = callback_query
        
        fake_update = FakeUpdate(query)
        return await admin_panel(fake_update, context)
    
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
        STRINGS['en']['broadcast_sent'].format(count=success_count),
        parse_mode='HTML'
    )
    
    return ADMIN_PANEL

def main():
    # Initialize database
    db_status = init_database()
    if not db_status:
        print("⚠️ Running without database - using fallback mode")
    
    # Get bot token from environment variable
    BOT_TOKEN = os.getenv("BOT_TOKEN", "7831518558:AAGhzqXl1HigurAIyUYjhdRqkShfeMwuKKM")
    
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN not found!")
        return

    try:
        print("🚀 Starting Premium IG Reporter Bot v2.0...")
        print(f"👑 Admin ID: {ADMIN_ID}")
        print("🗄️ MongoDB Database Integrated")
        
        # Create application with proper error handling
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        # Main conversation handler (simplified per_message settings)
        conv = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                REGISTER: [
                    CallbackQueryHandler(handle_language_selection, pattern='^lang_'),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration)
                ],
                MAIN_MENU: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_main_menu),
                    CallbackQueryHandler(handle_language_change, pattern='^change_lang_')
                ],
                REPORT_MENU: [CallbackQueryHandler(handle_report_menu)],
                USERNAME_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username_input)],
                REPORT_TYPE: [CallbackQueryHandler(handle_report_type, pattern='^type_')],
                IMPERSONATION_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_impersonation_url)],
                REPORT_LOOP: [CallbackQueryHandler(handle_report_loop)],
                ADMIN_PANEL: [CallbackQueryHandler(handle_admin_buttons)],
                BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast)],
                CUSTOMIZE_BUTTONS: [CallbackQueryHandler(handle_admin_buttons)]
            },
            fallbacks=[CommandHandler('start', start)],
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
                    print("⚠️ Polling conflict detected - Bot may already be running elsewhere")
                    print("💡 Keeping web server alive for deployment health checks")
                    print("🔄 If this persists, ensure only one bot instance is running")
                    
                    # Keep server alive for health checks
                    import time
                    while True:
                        time.sleep(60)
                        print("📡 Health server active - waiting...")
                else:
                    print(f"❌ Unexpected polling error: {error_str}")
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
