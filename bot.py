
import os
import json
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (ApplicationBuilder, CallbackContext, CommandHandler, MessageHandler, filters,
                          CallbackQueryHandler, ConversationHandler)
import random
import asyncio

# Constants
ADMIN_ID = 6881713177
DB_FILE = "db.json"

# States for ConversationHandler
LANGUAGE, USERNAME, REPORT_TYPE, IMPERSONATION_URL, CONFIRM, LOOP = range(6)

# Admin Panel States
ADMIN_PANEL, BROADCAST_MESSAGE, BROADCAST_MEDIA, SET_WELCOME_TEXT, SET_WELCOME_MEDIA = range(100, 105)

# Language strings
STRINGS = {
    'en': {
        'welcome': "🕵️ Welcome to AnonymousIGReport\nA premium IG report simulator bot.",
        'choose_lang': "Choose your language / कृपया भाषा चुनें:",
        'send_username': "Send the Instagram username you want to report:",
        'choose_report_type': "Select the report reason:",
        'ask_impersonation_url': "Send the link to the account being impersonated:",
        'confirm': "Press START to begin simulated reporting.",
        'start_report': "⚡ Starting simulation...",
        'stop_report': "❌ Reporting stopped.",
        'report_result': ["✅ Report sent successfully", "❌ Error sending report"],
        'admin_panel': "🛠 Admin Panel",
        'stats': "📊 Bot Stats:\nTotal Users: {total}\nActive (24h): {active}"
    },
    'hi': {
        'welcome': "🕵️ AnonymousIGReport में आपका स्वागत है\nएक प्रीमियम IG रिपोर्ट सिमुलेटर बॉट।",
        'choose_lang': "अपनी भाषा चुनें / Choose your language:",
        'send_username': "Instagram username भेजें जिसे आप रिपोर्ट करना चाहते हैं:",
        'choose_report_type': "रिपोर्ट का कारण चुनें:",
        'ask_impersonation_url': "उस अकाउंट का लिंक भेजें जिसकी नकल की जा रही है:",
        'confirm': "सिमुलेटेड रिपोर्टिंग शुरू करने के लिए START दबाएं।",
        'start_report': "⚡ सिमुलेशन शुरू हो रहा है...",
        'stop_report': "❌ रिपोर्टिंग बंद कर दी गई।",
        'report_result': ["✅ रिपोर्ट सफलतापूर्वक भेजी गई", "❌ रिपोर्ट भेजने में त्रुटि"],
        'admin_panel': "🛠 एडमिन पैनल",
        'stats': "📊 बॉट आंकड़े:\nकुल उपयोगकर्ता: {total}\nसक्रिय (24घं): {active}"
    }
}

# User session storage
sessions = {}

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

async def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    now = datetime.now().isoformat()
    
    if user_id not in user_db:
        user_db[user_id] = {
            "username": update.effective_user.username or "Unknown",
            "lang": "en",
            "joined_at": now,
            "last_active": now
        }
    else:
        user_db[user_id]["last_active"] = now
    
    save_db()

    keyboard = [
        [InlineKeyboardButton("English", callback_data='lang_en')],
        [InlineKeyboardButton("Hindi / हिंदी", callback_data='lang_hi')]
    ]
    
    await update.message.reply_text(
        STRINGS['en']['welcome'] + '\n\n' + STRINGS['en']['choose_lang'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return LANGUAGE

async def admin(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Access denied!")
        return ConversationHandler.END
        
    total_users = len(user_db)
    now = datetime.now()
    active_users = 0
    
    for user_data in user_db.values():
        try:
            last_active = datetime.fromisoformat(user_data['last_active'])
            if last_active > now - timedelta(hours=24):
                active_users += 1
        except:
            continue
    
    stats = STRINGS['en']['stats'].format(total=total_users, active=active_users)

    keyboard = [
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast_msg")],
        [InlineKeyboardButton("📊 User Stats", callback_data="admin_stats")]
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
    
    user_id = str(query.from_user.id)
    if user_id in user_db:
        user_db[user_id]['lang'] = lang
        user_db[user_id]['last_active'] = datetime.now().isoformat()
        save_db()
    
    await query.edit_message_text(STRINGS[lang]['send_username'])
    return USERNAME

async def receive_username(update: Update, context: CallbackContext):
    context.user_data['username'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    keyboard = [
        [InlineKeyboardButton("Hate Speech", callback_data='type_hate')],
        [InlineKeyboardButton("Self-Harm / Suicide", callback_data='type_selfharm')],
        [InlineKeyboardButton("Bullying", callback_data='type_bully')],
        [InlineKeyboardButton("Terrorism / Violence", callback_data='type_terrorism')],
        [InlineKeyboardButton("Impersonation", callback_data='type_impersonation')],
    ]
    
    await update.message.reply_text(
        STRINGS[lang]['choose_report_type'], 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return REPORT_TYPE

async def receive_report_type(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    report_type = query.data.split('_')[1]
    context.user_data['report_type'] = report_type
    lang = context.user_data.get('lang', 'en')

    if report_type == 'impersonation':
        await query.edit_message_text(STRINGS[lang]['ask_impersonation_url'])
        return IMPERSONATION_URL
    else:
        keyboard = [
            [InlineKeyboardButton("▶️ Start", callback_data='start')],
            [InlineKeyboardButton("⏹️ Stop", callback_data='stop')]
        ]
        await query.edit_message_text(
            STRINGS[lang]['confirm'], 
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return LOOP

async def receive_impersonation_url(update: Update, context: CallbackContext):
    context.user_data['impersonation_url'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    keyboard = [
        [InlineKeyboardButton("▶️ Start", callback_data='start')],
        [InlineKeyboardButton("⏹️ Stop", callback_data='stop')]
    ]
    
    await update.message.reply_text(
        STRINGS[lang]['confirm'], 
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return LOOP

async def handle_loop_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    lang = context.user_data.get('lang', 'en')
    await query.answer()

    if query.data == 'start':
        sessions[user_id] = True
        await query.edit_message_text(STRINGS[lang]['start_report'])
        
        # Simulate reporting process
        report_count = 0
        while sessions.get(user_id) and report_count < 10:  # Limit to prevent spam
            try:
                result = random.choice(STRINGS[lang]['report_result'])
                await context.bot.send_message(chat_id=user_id, text=f"{result} ({report_count + 1}/10)")
                await asyncio.sleep(random.randint(2, 5))
                report_count += 1
            except Exception as e:
                print(f"Error in reporting loop: {e}")
                break
                
        sessions[user_id] = False
        return LOOP
        
    elif query.data == 'stop':
        sessions[user_id] = False
        await query.edit_message_text(STRINGS[lang]['stop_report'])
        return LOOP

async def handle_admin_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_stats":
        total_users = len(user_db)
        await query.edit_message_text(f"📊 Total Users: {total_users}")
    
    return ADMIN_PANEL

def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN environment variable not found!")
        print("Please set your Telegram bot token in the environment variables.")
        return

    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        conv = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                LANGUAGE: [CallbackQueryHandler(set_language)],
                USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)],
                REPORT_TYPE: [CallbackQueryHandler(receive_report_type)],
                IMPERSONATION_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_impersonation_url)],
                LOOP: [CallbackQueryHandler(handle_loop_buttons)],
                ADMIN_PANEL: [CallbackQueryHandler(handle_admin_buttons)]
            },
            fallbacks=[CommandHandler('start', start)]
        )

        app.add_handler(conv)
        app.add_handler(CommandHandler("admin", admin))
        
        print("Bot started successfully!")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()
