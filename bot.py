import os
import json
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters,
                          CallbackQueryHandler, ConversationHandler)
import random
import asyncio

# Constants
ADMIN_ID = 6881713177
DB_FILE = "db.json"

# States for ConversationHandler
MAIN_MENU, REGISTER, PROFILE, REPORT_MENU, USERNAME_INPUT, REPORT_TYPE, IMPERSONATION_URL, REPORT_LOOP = range(8)

# Admin Panel States
ADMIN_PANEL, BROADCAST_MESSAGE, VIEW_USERS, USER_STATS = range(100, 104)

# Language strings
STRINGS = {
    'en': {
        'welcome': "🔥 <b>Welcome to Premium IG Reporter</b> 🔥\n\n🎯 <b>Ultimate Instagram Reporting Tool</b>\n\n⚡ Fast • 🔒 Anonymous • 💯 Effective",
        'register_prompt': "🎭 <b>Welcome New User!</b>\n\n📝 Please enter your <b>Display Name</b> to get started:",
        'registration_success': "🎉 <b>Registration Successful!</b>\n\n✅ Welcome aboard, <b>{name}</b>!\n🚀 You can now access all features.",
        'main_menu': "🏠 <b>Main Menu</b>\n\n👋 Welcome, <b>{name}</b>!\n🎯 Choose an option below:",
        'profile': "👤 <b>Your Profile</b>\n\n📝 Name: <b>{name}</b>\n📅 Joined: <b>{date}</b>\n⚡ Status: <b>Active</b>",
        'report_menu': "🎯 <b>Report Center</b>\n\n⚡ Choose your action:",
        'send_username': "📱 <b>Enter Target Username</b>\n\n🎯 Send the Instagram username to report:\n\n<i>Example: @username</i>",
        'choose_report_type': "⚔️ <b>Select Report Type</b>\n\n🎯 Choose violation category:",
        'ask_impersonation_url': "🔗 <b>Impersonation Details</b>\n\n📎 Send the link of the account being impersonated:",
        'confirm_start': "🚀 <b>Ready to Launch</b>\n\n🎯 Target: <b>@{username}</b>\n⚔️ Type: <b>{type}</b>\n\n✅ Press START to begin",
        'reporting_started': "⚡ <b>Report Attack Initiated</b>\n\n🎯 Target: <b>@{username}</b>\n🔥 Status: <b>ACTIVE</b>",
        'reporting_stopped': "⏹️ <b>Report Attack Stopped</b>\n\n📊 Session ended by user",
        'report_success': "✅ <b>Report #{count} Sent</b>\n🎯 Target: <b>@{username}</b>\n⚡ Status: <b>SUCCESS</b>",
        'report_failed': "❌ <b>Report #{count} Failed</b>\n🎯 Target: <b>@{username}</b>\n⚠️ Status: <b>RETRY</b>",
        'admin_panel': "🛠️ <b>Admin Control Panel</b>\n\n👑 Administrator Dashboard",
        'user_stats': "📊 <b>Bot Statistics</b>\n\n👥 Total Users: <b>{total}</b>\n⚡ Active (24h): <b>{active}</b>\n📅 Today's Joins: <b>{today}</b>"
    },
    'hi': {
        'welcome': "🔥 <b>Premium IG Reporter में आपका स्वागत है</b> 🔥\n\n🎯 <b>Ultimate Instagram Reporting Tool</b>\n\n⚡ तेज • 🔒 गुमनाम • 💯 प्रभावी",
        'register_prompt': "🎭 <b>नए उपयोगकर्ता का स्वागत है!</b>\n\n📝 कृपया अपना <b>नाम</b> दर्ज करें:",
        'registration_success': "🎉 <b>पंजीकरण सफल!</b>\n\n✅ स्वागत है, <b>{name}</b>!\n🚀 अब आप सभी फीचर्स का उपयोग कर सकते हैं।",
        'main_menu': "🏠 <b>मुख्य मेनू</b>\n\n👋 स्वागत है, <b>{name}</b>!\n🎯 नीचे से विकल्प चुनें:",
        'profile': "👤 <b>आपकी प्रोफाइल</b>\n\n📝 नाम: <b>{name}</b>\n📅 शामिल: <b>{date}</b>\n⚡ स्थिति: <b>सक्रिय</b>",
        'report_menu': "🎯 <b>रिपोर्ट सेंटर</b>\n\n⚡ अपनी कार्रवाई चुनें:",
        'send_username': "📱 <b>Target Username दर्ज करें</b>\n\n🎯 Instagram username भेजें:\n\n<i>उदाहरण: @username</i>",
        'choose_report_type': "⚔️ <b>रिपोर्ट प्रकार चुनें</b>\n\n🎯 उल्लंघन श्रेणी चुनें:",
        'ask_impersonation_url': "🔗 <b>Impersonation विवरण</b>\n\n📎 उस अकाउंट का लिंक भेजें जिसकी नकल की जा रही है:",
        'confirm_start': "🚀 <b>लॉन्च के लिए तैयार</b>\n\n🎯 Target: <b>@{username}</b>\n⚔️ प्रकार: <b>{type}</b>\n\n✅ START दबाएं",
        'reporting_started': "⚡ <b>रिपोर्ट अटैक शुरू</b>\n\n🎯 Target: <b>@{username}</b>\n🔥 स्थिति: <b>सक्रिय</b>",
        'reporting_stopped': "⏹️ <b>रिपोर्ट अटैक बंद</b>\n\n📊 सेशन समाप्त",
        'report_success': "✅ <b>रिपोर्ट #{count} भेजी गई</b>\n🎯 Target: <b>@{username}</b>\n⚡ स्थिति: <b>सफल</b>",
        'report_failed': "❌ <b>रिपोर्ट #{count} असफल</b>\n🎯 Target: <b>@{username}</b>\n⚠️ स्थिति: <b>पुनः प्रयास</b>",
        'admin_panel': "🛠️ <b>एडमिन कंट्रोल पैनल</b>\n\n👑 प्रशासक डैशबोर्ड",
        'user_stats': "📊 <b>बॉट आंकड़े</b>\n\n👥 कुल उपयोगकर्ता: <b>{total}</b>\n⚡ सक्रिय (24घं): <b>{active}</b>\n📅 आज के नए: <b>{today}</b>"
    }
}

# Report types with emojis
REPORT_TYPES = {
    'hate': '😡 Hate Speech / नफरत फैलाना',
    'selfharm': '🆘 Self-Harm / आत्म-हानि',
    'bully': '👊 Bullying / धमकाना',
    'terrorism': '💣 Terrorism / आतंकवाद',
    'impersonation': '🎭 Impersonation / नकल',
    'spam': '📧 Spam / स्पैम',
    'violence': '⚔️ Violence / हिंसा',
    'drugs': '💊 Drugs / नशा'
}

# User session storage
sessions = {}
active_reports = {}

# Load/Save user data
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

user_db = load_db()

def save_db():
    try:
        with open(DB_FILE, "w") as f:
            json.dump(user_db, f, indent=2)
    except Exception as e:
        print(f"Error saving database: {e}")

def get_main_keyboard(lang='en'):
    if lang == 'hi':
        return ReplyKeyboardMarkup([
            [KeyboardButton("🎯 रिपोर्ट करें"), KeyboardButton("👤 प्रोफाइल")],
            [KeyboardButton("📊 मेरी रिपोर्ट्स"), KeyboardButton("🏠 होम")],
            [KeyboardButton("🌐 भाषा बदलें"), KeyboardButton("ℹ️ सहायता")]
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup([
            [KeyboardButton("🎯 Start Report"), KeyboardButton("👤 Profile")],
            [KeyboardButton("📊 My Reports"), KeyboardButton("🏠 Home")],
            [KeyboardButton("🌐 Language"), KeyboardButton("ℹ️ Help")]
        ], resize_keyboard=True)

async def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    now = datetime.now().isoformat()
    
    # Check if user exists
    if user_id not in user_db:
        keyboard = [
            [InlineKeyboardButton("🇺🇸 English", callback_data='lang_en')],
            [InlineKeyboardButton("🇮🇳 हिंदी", callback_data='lang_hi')]
        ]
        
        await update.message.reply_text(
            STRINGS['en']['welcome'] + '\n\n🌐 <b>Choose Language / भाषा चुनें:</b>',
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return REGISTER
    else:
        # Update last active
        user_db[user_id]["last_active"] = now
        save_db()
        
        lang = user_db[user_id].get('lang', 'en')
        name = user_db[user_id].get('display_name', 'User')
        
        await update.message.reply_text(
            STRINGS[lang]['main_menu'].format(name=name),
            reply_markup=get_main_keyboard(lang),
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
    now = datetime.now().isoformat()
    
    # Save user data
    user_db[user_id] = {
        "username": update.effective_user.username or "Unknown",
        "display_name": display_name,
        "lang": lang,
        "joined_at": now,
        "last_active": now,
        "total_reports": 0
    }
    save_db()
    
    await update.message.reply_text(
        STRINGS[lang]['registration_success'].format(name=display_name),
        parse_mode='HTML'
    )
    
    await asyncio.sleep(2)
    
    await update.message.reply_text(
        STRINGS[lang]['main_menu'].format(name=display_name),
        reply_markup=get_main_keyboard(lang),
        parse_mode='HTML'
    )
    return MAIN_MENU

async def handle_main_menu(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    user_data = user_db.get(user_id, {})
    lang = user_data.get('lang', 'en')
    name = user_data.get('display_name', 'User')
    text = update.message.text
    
    if text in ["🎯 Start Report", "🎯 रिपोर्ट करें"]:
        await update.message.reply_text(
            STRINGS[lang]['report_menu'],
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🚀 New Report / नई रिपोर्ट", callback_data="new_report")
            ]]),
            parse_mode='HTML'
        )
        return REPORT_MENU
        
    elif text in ["👤 Profile", "👤 प्रोफाइल"]:
        join_date = datetime.fromisoformat(user_data.get('joined_at', '')).strftime('%d/%m/%Y')
        await update.message.reply_text(
            STRINGS[lang]['profile'].format(name=name, date=join_date),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif text in ["🏠 Home", "🏠 होम"]:
        await update.message.reply_text(
            STRINGS[lang]['main_menu'].format(name=name),
            reply_markup=get_main_keyboard(lang),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif text in ["🌐 Language", "🌐 भाषा बदलें"]:
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
    lang = user_db.get(user_id, {}).get('lang', 'en')
    
    if query.data == "new_report":
        await query.edit_message_text(
            STRINGS[lang]['send_username'],
            parse_mode='HTML'
        )
        return USERNAME_INPUT

async def handle_username_input(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    lang = user_db.get(user_id, {}).get('lang', 'en')
    username = update.message.text.strip().replace('@', '')
    
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
    lang = user_db.get(user_id, {}).get('lang', 'en')
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
            [InlineKeyboardButton("🚀 START", callback_data='start_report')],
            [InlineKeyboardButton("❌ CANCEL", callback_data='cancel_report')]
        ]
        
        await query.edit_message_text(
            STRINGS[lang]['confirm_start'].format(username=username, type=type_name),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return REPORT_LOOP

async def handle_impersonation_url(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    lang = user_db.get(user_id, {}).get('lang', 'en')
    
    context.user_data['impersonation_url'] = update.message.text
    username = context.user_data['target_username']
    
    keyboard = [
        [InlineKeyboardButton("🚀 START", callback_data='start_report')],
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
    lang = user_db.get(user_id, {}).get('lang', 'en')
    username = context.user_data.get('target_username', '')
    
    if query.data == 'start_report':
        # Start infinite reporting
        active_reports[user_id] = True
        
        keyboard = [[InlineKeyboardButton("⏹️ STOP REPORT", callback_data='stop_report')]]
        
        await query.edit_message_text(
            STRINGS[lang]['reporting_started'].format(username=username),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
        # Start the infinite reporting loop
        await start_infinite_reporting(context, user_id, username, lang)
        
    elif query.data == 'stop_report':
        active_reports[user_id] = False
        await query.edit_message_text(
            STRINGS[lang]['reporting_stopped'],
            parse_mode='HTML'
        )
        
        # Return to main menu
        name = user_db.get(user_id, {}).get('display_name', 'User')
        await context.bot.send_message(
            chat_id=user_id,
            text=STRINGS[lang]['main_menu'].format(name=name),
            reply_markup=get_main_keyboard(lang),
            parse_mode='HTML'
        )
        return MAIN_MENU
        
    elif query.data == 'cancel_report':
        name = user_db.get(user_id, {}).get('display_name', 'User')
        await query.edit_message_text(
            STRINGS[lang]['main_menu'].format(name=name),
            parse_mode='HTML'
        )
        return MAIN_MENU
    
    return REPORT_LOOP

async def start_infinite_reporting(context: CallbackContext, user_id: str, username: str, lang: str):
    report_count = 0
    
    while active_reports.get(user_id, False):
        try:
            report_count += 1
            
            # Random success/failure
            if random.choice([True, False, True]):  # 66% success rate
                message = STRINGS[lang]['report_success'].format(count=report_count, username=username)
            else:
                message = STRINGS[lang]['report_failed'].format(count=report_count, username=username)
            
            await context.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='HTML'
            )
            
            # Update user stats
            if user_id in user_db:
                user_db[user_id]['total_reports'] = user_db[user_id].get('total_reports', 0) + 1
                save_db()
            
            # Random delay between 1-3 seconds
            await asyncio.sleep(random.uniform(1.0, 3.0))
            
        except Exception as e:
            print(f"Error in reporting loop: {e}")
            break

async def handle_language_change(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    new_lang = query.data.split('_')[2]
    
    if user_id in user_db:
        user_db[user_id]['lang'] = new_lang
        save_db()
    
    name = user_db.get(user_id, {}).get('display_name', 'User')
    
    await query.edit_message_text(
        STRINGS[new_lang]['main_menu'].format(name=name),
        parse_mode='HTML'
    )
    
    await context.bot.send_message(
        chat_id=user_id,
        text=STRINGS[new_lang]['main_menu'].format(name=name),
        reply_markup=get_main_keyboard(new_lang),
        parse_mode='HTML'
    )
    
    return MAIN_MENU

# Admin functions
async def admin(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ <b>Access Denied!</b>", parse_mode='HTML')
        return ConversationHandler.END
    
    total_users = len(user_db)
    now = datetime.now()
    active_users = 0
    today_joins = 0
    
    for user_data in user_db.values():
        try:
            last_active = datetime.fromisoformat(user_data.get('last_active', ''))
            if last_active > now - timedelta(hours=24):
                active_users += 1
                
            joined = datetime.fromisoformat(user_data.get('joined_at', ''))
            if joined.date() == now.date():
                today_joins += 1
        except:
            continue
    
    stats = STRINGS['en']['user_stats'].format(
        total=total_users, 
        active=active_users, 
        today=today_joins
    )
    
    keyboard = [
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👥 View Users", callback_data="admin_users")],
        [InlineKeyboardButton("📊 Detailed Stats", callback_data="admin_detailed_stats")]
    ]
    
    await update.message.reply_text(
        STRINGS['en']['admin_panel'] + "\n\n" + stats,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return ADMIN_PANEL

async def handle_admin_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_detailed_stats":
        stats_text = "📊 <b>Detailed Statistics</b>\n\n"
        
        for user_id, data in user_db.items():
            name = data.get('display_name', 'Unknown')
            reports = data.get('total_reports', 0)
            lang = data.get('lang', 'en')
            stats_text += f"👤 <b>{name}</b>\n"
            stats_text += f"   🆔 ID: {user_id}\n"
            stats_text += f"   📊 Reports: {reports}\n"
            stats_text += f"   🌐 Lang: {lang}\n\n"
        
        await query.edit_message_text(stats_text[:4000], parse_mode='HTML')
    
    return ADMIN_PANEL

def main():
    # Get bot token from environment
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ ERROR: BOT_TOKEN environment variable not found!")
        print("📝 Please set your Telegram bot token in the environment variables.")
        return

    try:
        print("🚀 Starting Premium IG Reporter Bot...")
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        # Main conversation handler
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
                ADMIN_PANEL: [CallbackQueryHandler(handle_admin_buttons)]
            },
            fallbacks=[CommandHandler('start', start)]
        )

        app.add_handler(conv)
        app.add_handler(CommandHandler("admin", admin))
        
        print("✅ Bot started successfully!")
        print(f"👑 Admin ID: {ADMIN_ID}")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

if __name__ == "__main__":
    main()
