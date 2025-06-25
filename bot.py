import os
import json
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputFile
from telegram.ext import (ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters,
                          CallbackQueryHandler, ConversationHandler)
import random, asyncio

# Constants
ADMIN_ID = 6881713177
DB_FILE = "db.json"

# States for ConversationHandler
LANGUAGE, USERNAME, REPORT_TYPE, IMPERSONATION_URL, CONFIRM, LOOP = range(6)

# Admin Panel States
ADMIN_PANEL, BROADCAST_MESSAGE, BROADCAST_MEDIA, SET_WELCOME_TEXT, SET_WELCOME_MEDIA = range(100, 105)

# Language strings (add Hindi/other languages here)
STRINGS = {
    'en': {
        'welcome': "\U0001F575\ufe0f Welcome to AnonymousIGRepor\nA premium IG report simulator bot.",
        'choose_lang': "Choose your language / \u0915\u0943\u092a\u092f\u093e \u092d\u093e\u0937\u093e \u091a\u0941\u0928\u0947\u0902:",
        'send_username': "Send the Instagram username you want to report:",
        'choose_report_type': "Select the report reason:",
        'ask_impersonation_url': "Send the link to the account being impersonated:",
        'confirm': "Press START to begin simulated reporting.",
        'start_report': "\u26a1 Starting simulation...",
        'stop_report': "\u274c Reporting stopped.",
        'report_result': ["✅ Report sent successfully", "❌ Error sending report"],
        'admin_panel': "\U0001F6E0 Admin Panel",
        'stats': "\U0001F4CA Bot Stats:\nTotal Users: {total}\nActive (24h): {active}"
    }
}

# User session storage
sessions = {}

# Load/Save user data
if os.path.exists(DB_FILE):
    with open(DB_FILE, "r") as f:
        user_db = json.load(f)
else:
    user_db = {}

def save_db():
    with open(DB_FILE, "w") as f:
        json.dump(user_db, f)

async def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    now = datetime.now().isoformat()
    if user_id not in user_db:
        user_db[user_id] = {
            "username": update.effective_user.username,
            "lang": "en",
            "joined_at": now,
            "last_active": now
        }
    else:
        user_db[user_id]["last_active"] = now
    save_db()

    keyboard = [
        [InlineKeyboardButton("English", callback_data='lang_en')],
        [InlineKeyboardButton("Hindi / \u0939\u093f\u0902\u0926\u0940", callback_data='lang_hi')]
    ]
    await update.message.reply_text(
        STRINGS['en']['welcome'] + '\n\n' + STRINGS['en']['choose_lang'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return LANGUAGE

async def admin(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    total_users = len(user_db)
    now = datetime.now()
    active_users = sum(1 for u in user_db.values() if datetime.fromisoformat(u['last_active']) > now - timedelta(hours=24))
    stats = STRINGS['en']['stats'].format(total=total_users, active=active_users)

    keyboard = [
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast_msg")],
        [InlineKeyboardButton("🎞️ Broadcast Media", callback_data="admin_broadcast_media")],
        [InlineKeyboardButton("📝 Edit Welcome Text", callback_data="admin_set_welcome_text")],
        [InlineKeyboardButton("🎬 Update Welcome Media", callback_data="admin_set_welcome_media")]
    ]
    await update.message.reply_text(
        stats + "\n\nSelect an action:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ADMIN_PANEL

async def set_language(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    lang = query.data.split('_')[1]
    context.user_data['lang'] = lang
    user_db[str(query.from_user.id)]['lang'] = lang
    user_db[str(query.from_user.id)]['last_active'] = datetime.now().isoformat()
    save_db()
    await query.edit_message_text(STRINGS[lang]['send_username'])
    return USERNAME

async def receive_username(update: Update, context: CallbackContext):
    context.user_data['username'] = update.message.text
    lang = context.user_data['lang']
    keyboard = [
        [InlineKeyboardButton("Hate Speech", callback_data='type_hate')],
        [InlineKeyboardButton("Self-Harm / Suicide", callback_data='type_selfharm')],
        [InlineKeyboardButton("Bullying", callback_data='type_bully')],
        [InlineKeyboardButton("Terrorism / Violence", callback_data='type_terrorism')],
        [InlineKeyboardButton("Impersonation", callback_data='type_impersonation')],
    ]
    await update.message.reply_text(STRINGS[lang]['choose_report_type'], reply_markup=InlineKeyboardMarkup(keyboard))
    return REPORT_TYPE

async def receive_report_type(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    report_type = query.data.split('_')[1]
    context.user_data['report_type'] = report_type
    lang = context.user_data['lang']

    if report_type == 'impersonation':
        await query.edit_message_text(STRINGS[lang]['ask_impersonation_url'])
        return IMPERSONATION_URL
    else:
        await query.edit_message_text(STRINGS[lang]['confirm'], reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Start", callback_data='start')],
            [InlineKeyboardButton("⏹️ Stop", callback_data='stop')]
        ]))
        return LOOP

async def receive_impersonation_url(update: Update, context: CallbackContext):
    context.user_data['impersonation_url'] = update.message.text
    lang = context.user_data['lang']
    await update.message.reply_text(STRINGS[lang]['confirm'], reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Start", callback_data='start')],
        [InlineKeyboardButton("⏹️ Stop", callback_data='stop')]
    ]))
    return LOOP

async def handle_loop_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    lang = context.user_data['lang']
    await query.answer()

    if query.data == 'start':
        sessions[user_id] = True
        await query.edit_message_text(STRINGS[lang]['start_report'])
        while sessions.get(user_id):
            result = random.choice(STRINGS[lang]['report_result'])
            await context.bot.send_message(chat_id=user_id, text=result)
            await asyncio.sleep(random.randint(2, 4))
        return LOOP
    else:
        sessions[user_id] = False
        await query.edit_message_text(STRINGS[lang]['stop_report'])
        return LOOP

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN environment variable not found!")
    print("Please set your Telegram bot token in the environment variables.")
    exit(1)

app = ApplicationBuilder().token(BOT_TOKEN).build()

conv = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        LANGUAGE: [CallbackQueryHandler(set_language)],
        USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)],
        REPORT_TYPE: [CallbackQueryHandler(receive_report_type)],
        IMPERSONATION_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_impersonation_url)],
        LOOP: [CallbackQueryHandler(handle_loop_buttons)],
        ADMIN_PANEL: [CallbackQueryHandler(admin)]
    },
    fallbacks=[]
)

app.add_handler(conv)
app.add_handler(CommandHandler("admin", admin))
app.run_polling()
