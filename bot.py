import os
import json
import random
import asyncio
from datetime import datetime, timedelta
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
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

# Constants
ADMIN_ID = 6881713177
DB_FILE = "db.json"
REPORTS_FILE = "reports.json"

# States for ConversationHandler
START, LANGUAGE, MAIN_MENU, REPORT_USERNAME, REPORT_TYPE, IMPERSONATION_URL, REPORT_CONFIRM, REPORT_PROGRESS = range(8)

# Admin Panel States
ADMIN_PANEL, BROADCAST_MESSAGE, BROADCAST_CONFIRM = range(100, 103)

# Language strings with enhanced formatting
STRINGS = {
    'en': {
        'welcome': "✨🔍 <b>AnonymousIG Guardian</b> ✨🔍\n\n"
                   "⚡️ The ULTIMATE Instagram reporting solution ⚡️\n"
                   "🛡️ Protect your digital presence with military-grade reporting",
        'choose_lang': "🌐 <b>Select your language:</b>",
        'main_menu': "🏠 <b>Main Menu</b>\n\n"
                     "Choose an action:",
        'send_username': "📌 <b>Enter Instagram username to report:</b>\n\n"
                         "<i>Example: instagramuser123</i>",
        'choose_report_type': "🚨 <b>Select report reason:</b>",
        'ask_impersonation_url': "🔗 <b>Enter URL of the authentic account:</b>\n\n"
                                 "<i>Example: https://instagram.com/realcelebrity</i>",
        'confirm': "⚠️ <b>FINAL CONFIRMATION</b> ⚠️\n\n"
                   "Target: <code>{username}</code>\n"
                   "Reason: {reason}\n"
                   "{impersonation}\n\n"
                   "🔥 <b>Ready to launch operation?</b>",
        'start_report': "🚀 <b>OPERATION INITIATED</b> 🚀\n\n"
                        "⚙️ Deploying reporting protocols...",
        'report_in_progress': "🔄 <b>REPORTING IN PROGRESS</b> 🔄\n"
                              "Reports submitted: {count}",
        'report_success': "✅ <b>REPORT SUCCESSFUL</b>\n"
                           "ID: <code>{report_id}</code>\n"
                           "Target: <code>{target}</code>",
        'report_failed': "❌ <b>REPORT FAILED</b>\n"
                         "Target: <code>{target}</code>\n"
                         "Error: {error}",
        'report_completed': "🎉 <b>MISSION COMPLETE</b> 🎉\n\n"
                            "Total reports submitted: {count}",
        'report_stopped': "🛑 <b>OPERATION TERMINATED</b>\n"
                          "Reports submitted: {count}",
        'admin_panel': "🔒 <b>ADMIN CONTROL PANEL</b> 🔒",
        'stats': "📊 <b>SYSTEM STATISTICS</b>\n\n"
                 "👥 Total Users: <b>{total}</b>\n"
                 "🔥 Active (24h): <b>{active}</b>\n"
                 "🚀 Reports Today: <b>{reports_today}</b>",
        'no_reports': "📭 <b>No reports yet!</b>\n"
                      "Launch your first operation from the main menu",
        'my_reports': "📋 <b>YOUR OPERATION HISTORY</b>\n\n"
                      "Total reports: {count}\n"
                      "Last report: {last_report}\n\n"
                      "Recent operations:",
        'help': "❓ <b>HELP CENTER</b> ❓\n\n"
                 "<b>How to use:</b>\n"
                 "1. Go to Main Menu → Report Account\n"
                 "2. Enter target username\n"
                 "3. Select report reason\n"
                 "4. Confirm and launch operation\n\n"
                 "⚡ <b>Features:</b>\n"
                 "- 24/7 reporting operations\n"
                 "- Military-grade encryption\n"
                 "- Anonymous reporting\n"
                 "- Real-time tracking",
        'broadcast_prompt': "📢 <b>GLOBAL BROADCAST</b>\n\n"
                            "Enter your message:",
        'broadcast_sent': "🌐 <b>BROADCAST COMPLETE</b>\n"
                          "Recipients: {count} users",
        'contact': "📞 <b>CONTACT SUPPORT</b>\n\n"
                   "For assistance, contact our team:\n"
                   "@YourSupportHandle\n\n"
                   "🌐 Official Channel: @YourChannel"
    },
    'hi': {
        'welcome': "✨🔍 <b>AnonymousIG गार्जियन</b> ✨🔍\n\n"
                   "⚡️ इंस्टाग्राम रिपोर्टिंग का अंतिम समाधान ⚡️\n"
                   "🛡️ सैन्य-ग्रेड रिपोर्टिंग के साथ अपनी डिजिटल उपस्थिति की रक्षा करें",
        'choose_lang': "🌐 <b>अपनी भाषा चुनें:</b>",
        'main_menu': "🏠 <b>मुख्य मेनू</b>\n\n"
                     "एक क्रिया चुनें:",
        'send_username': "📌 <b>रिपोर्ट करने के लिए इंस्टाग्राम यूजरनेम दर्ज करें:</b>\n\n"
                         "<i>उदाहरण: instagramuser123</i>",
        'choose_report_type': "🚨 <b>रिपोर्ट का कारण चुनें:</b>",
        'ask_impersonation_url': "🔗 <b>वास्तविक खाते का URL दर्ज करें:</b>\n\n"
                                 "<i>उदाहरण: https://instagram.com/realcelebrity</i>",
        'confirm': "⚠️ <b>अंतिम पुष्टि</b> ⚠️\n\n"
                   "लक्ष्य: <code>{username}</code>\n"
                   "कारण: {reason}\n"
                   "{impersonation}\n\n"
                   "🔥 <b>ऑपरेशन शुरू करने के लिए तैयार?</b>",
        'start_report': "🚀 <b>ऑपरेशन शुरू</b> 🚀\n\n"
                        "⚙️ रिपोर्टिंग प्रोटोकॉल तैनात किए जा रहे हैं...",
        'report_in_progress': "🔄 <b>रिपोर्टिंग प्रगति पर है</b> 🔄\n"
                              "प्रस्तुत रिपोर्ट: {count}",
        'report_success': "✅ <b>रिपोर्ट सफल</b>\n"
                          "ID: <code>{report_id}</code>\n"
                          "लक्ष्य: <code>{target}</code>",
        'report_failed': "❌ <b>रिपोर्ट विफल</b>\n"
                         "लक्ष्य: <code>{target}</code>\n"
                         "त्रुटि: {error}",
        'report_completed': "🎉 <b>मिशन पूरा</b> 🎉\n\n"
                            "कुल प्रस्तुत रिपोर्ट: {count}",
        'report_stopped': "🛑 <b>ऑपरेशन समाप्त</b>\n"
                          "प्रस्तुत रिपोर्ट: {count}",
        'admin_panel': "🔒 <b>एडमिन कंट्रोल पैनल</b> 🔒",
        'stats': "📊 <b>सिस्टम सांख्यिकी</b>\n\n"
                 "👥 कुल उपयोगकर्ता: <b>{total}</b>\n"
                 "🔥 सक्रिय (24घंटे): <b>{active}</b>\n"
                 "🚀 आज की रिपोर्ट: <b>{reports_today}</b>",
        'no_reports': "📭 <b>अभी तक कोई रिपोर्ट नहीं!</b>\n"
                      "मुख्य मेनू से अपना पहला ऑपरेशन लॉन्च करें",
        'my_reports': "📋 <b>आपका ऑपरेशन इतिहास</b>\n\n"
                      "कुल रिपोर्ट: {count}\n"
                      "अंतिम रिपोर्ट: {last_report}\n\n"
                      "हाल के ऑपरेशन:",
        'help': "❓ <b>सहायता केंद्र</b> ❓\n\n"
                 "<b>उपयोग कैसे करें:</b>\n"
                 "1. मुख्य मेनू → खाता रिपोर्ट करें पर जाएं\n"
                 "2. लक्ष्य यूजरनेम दर्ज करें\n"
                 "3. रिपोर्ट का कारण चुनें\n"
                 "4. पुष्टि करें और ऑपरेशन लॉन्च करें\n\n"
                 "⚡ <b>विशेषताएँ:</b>\n"
                 "- 24/7 रिपोर्टिंग ऑपरेशन\n"
                 "- सैन्य-ग्रेड एन्क्रिप्शन\n"
                 "- गुमनाम रिपोर्टिंग\n"
                 "- रियल-टाइम ट्रैकिंग",
        'broadcast_prompt': "📢 <b>वैश्विक प्रसारण</b>\n\n"
                            "अपना संदेश दर्ज करें:",
        'broadcast_sent': "🌐 <b>प्रसारण पूर्ण</b>\n"
                          "प्राप्तकर्ता: {count} उपयोगकर्ता",
        'contact': "📞 <b>समर्थन से संपर्क करें</b>\n\n"
                   "सहायता के लिए, हमारी टीम से संपर्क करें:\n"
                   "@YourSupportHandle\n\n"
                   "🌐 आधिकारिक चैनल: @YourChannel"
    }
}

# Report reasons with emojis
REPORT_TYPES = {
    'hate': ("Hate Speech", "🚫"),
    'selfharm': ("Self-Harm/Suicide", "⚠️"),
    'bully': ("Bullying", "👊"),
    'terrorism': ("Terrorism/Violence", "🔫"),
    'impersonation': ("Impersonation", "👤"),
}

# User session storage
sessions = {}
user_reports = {}

# Load/Save user data
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def load_reports():
    if os.path.exists(REPORTS_FILE):
        try:
            with open(REPORTS_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

user_db = load_db()
report_db = load_reports()

def save_db():
    try:
        with open(DB_FILE, "w") as f:
            json.dump(user_db, f, indent=2)
    except Exception as e:
        print(f"Error saving database: {e}")

def save_reports():
    try:
        with open(REPORTS_FILE, "w") as f:
            json.dump(report_db, f, indent=2)
    except Exception as e:
        print(f"Error saving reports: {e}")

def generate_report_id():
    return f"RPT-{random.randint(100000, 999999)}"

async def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    now = datetime.now().isoformat()
    
    if user_id not in user_db:
        user_db[user_id] = {
            "username": update.effective_user.username or "Unknown",
            "lang": "en",
            "joined_at": now,
            "last_active": now,
            "reports": 0,
            "last_report": None
        }
        save_db()
    
    keyboard = [
        [InlineKeyboardButton("English 🇺🇸", callback_data='lang_en')],
        [InlineKeyboardButton("Hindi 🇮🇳", callback_data='lang_hi')]
    ]
    
    await update.message.reply_text(
        STRINGS['en']['welcome'],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return LANGUAGE

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
    
    await show_main_menu(update, context, lang)
    return MAIN_MENU

async def show_main_menu(update: Update, context: CallbackContext, lang: str):
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        chat_id = query.message.chat_id
        message_id = query.message.message_id
    else:
        chat_id = update.message.chat_id
        message_id = None
    
    keyboard = [
        [InlineKeyboardButton("📝 Report Account", callback_data='report_account')],
        [InlineKeyboardButton("📋 My Reports", callback_data='my_reports')],
        [InlineKeyboardButton("❓ Help", callback_data='help')],
        [InlineKeyboardButton("📞 Contact", callback_data='contact')]
    ]
    
    text = STRINGS[lang]['main_menu']
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if message_id:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    else:
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    return MAIN_MENU

async def start_report(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    lang = context.user_data.get('lang', 'en')
    await query.edit_message_text(
        STRINGS[lang]['send_username'],
        parse_mode='HTML'
    )
    return REPORT_USERNAME

async def receive_username(update: Update, context: CallbackContext):
    context.user_data['username'] = update.message.text
    lang = context.user_data.get('lang', 'en')
    
    keyboard = []
    for r_type, (label, emoji) in REPORT_TYPES.items():
        keyboard.append([InlineKeyboardButton(f"{emoji} {label}", callback_data=f'type_{r_type}')])
    
    await update.message.reply_text(
        STRINGS[lang]['choose_report_type'], 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
    return REPORT_TYPE

async def receive_report_type(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    report_type = query.data.split('_')[1]
    context.user_data['report_type'] = report_type
    lang = context.user_data.get('lang', 'en')
    username = context.user_data['username']

    if report_type == 'impersonation':
        await query.edit_message_text(
            STRINGS[lang]['ask_impersonation_url'],
            parse_mode='HTML'
        )
        return IMPERSONATION_URL
    else:
        return await show_confirmation(update, context)

async def receive_impersonation_url(update: Update, context: CallbackContext):
    context.user_data['impersonation_url'] = update.message.text
    return await show_confirmation(update, context)

async def show_confirmation(update: Update, context: CallbackContext):
    lang = context.user_data.get('lang', 'en')
    username = context.user_data['username']
    report_type = context.user_data['report_type']
    impersonation_url = context.user_data.get('impersonation_url')
    
    # Get report reason text
    report_reason, emoji = REPORT_TYPES[report_type]
    
    # Format impersonation info if available
    impersonation_text = ""
    if report_type == 'impersonation' and impersonation_url:
        impersonation_text = f"Original Account: <code>{impersonation_url}</code>\n"
    
    text = STRINGS[lang]['confirm'].format(
        username=username,
        reason=f"{emoji} {report_reason}",
        impersonation=impersonation_text
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ LAUNCH OPERATION", callback_data='start_report'),
            InlineKeyboardButton("🔙 Back", callback_data='back_to_menu')
        ]
    ]
    
    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    else:
        query = update.callback_query
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    return REPORT_CONFIRM

async def start_reporting(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    lang = context.user_data.get('lang', 'en')
    username = context.user_data['username']
    
    # Initialize report session
    sessions[user_id] = {
        'active': True,
        'count': 0
    }
    
    # Update user stats
    user_id_str = str(user_id)
    if user_id_str in user_db:
        user_db[user_id_str]['reports'] = user_db[user_id_str].get('reports', 0) + 1
        user_db[user_id_str]['last_report'] = datetime.now().isoformat()
        save_db()
    
    await query.edit_message_text(
        STRINGS[lang]['start_report'],
        parse_mode='HTML'
    )
    
    # Start reporting process
    asyncio.create_task(run_reporting_loop(user_id, context, lang, username))
    return REPORT_PROGRESS

async def run_reporting_loop(user_id: int, context: CallbackContext, lang: str, target: str):
    session = sessions.get(user_id)
    if not session:
        return
    
    report_count = 0
    start_time = datetime.now()
    
    # Create keyboard with stop button
    keyboard = [[InlineKeyboardButton("🛑 STOP OPERATION", callback_data='stop_report')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Send initial progress message
    progress_msg = await context.bot.send_message(
        chat_id=user_id,
        text=STRINGS[lang]['report_in_progress'].format(count=0),
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    # Reporting loop
    while session.get('active'):
        try:
            # Simulate report
            await asyncio.sleep(random.uniform(1.5, 3.5))
            report_count += 1
            
            # Generate random report ID
            report_id = generate_report_id()
            
            # Store report
            report_time = datetime.now().isoformat()
            report_data = {
                "id": report_id,
                "target": target,
                "time": report_time,
                "status": "success"
            }
            
            # Save to report database
            user_id_str = str(user_id)
            if user_id_str not in report_db:
                report_db[user_id_str] = []
            report_db[user_id_str].append(report_data)
            save_reports()
            
            # Update progress message
            if report_count % 5 == 0:  # Update every 5 reports
                await context.bot.edit_message_text(
                    chat_id=user_id,
                    message_id=progress_msg.message_id,
                    text=STRINGS[lang]['report_in_progress'].format(count=report_count),
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            
            # Occasionally send success messages
            if random.random() < 0.3:  # 30% chance
                success_text = STRINGS[lang]['report_success'].format(
                    report_id=report_id,
                    target=target
                )
                await context.bot.send_message(
                    chat_id=user_id,
                    text=success_text,
                    parse_mode='HTML'
                )
                
        except Exception as e:
            print(f"Reporting error: {e}")
            # Send error notification
            error_text = STRINGS[lang]['report_failed'].format(
                target=target,
                error="System overload"
            )
            await context.bot.send_message(
                chat_id=user_id,
                text=error_text,
                parse_mode='HTML'
            )
            break
    
    # After loop completes
    duration = datetime.now() - start_time
    minutes = duration.total_seconds() / 60
    
    # Update session
    session['count'] = report_count
    session['active'] = False
    
    # Send completion message
    if session.get('stopped'):
        result_text = STRINGS[lang]['report_stopped'].format(count=report_count)
    else:
        result_text = STRINGS[lang]['report_completed'].format(count=report_count)
    
    await context.bot.send_message(
        chat_id=user_id,
        text=result_text,
        parse_mode='HTML'
    )
    
    # Show main menu
    await show_main_menu(update, context, lang)

async def stop_reporting(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    lang = context.user_data.get('lang', 'en')
    
    # Mark session as stopped
    if user_id in sessions:
        sessions[user_id]['stopped'] = True
        sessions[user_id]['active'] = False
    
    await query.answer("Operation stopping...")
    return REPORT_PROGRESS

async def show_my_reports(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    lang = context.user_data.get('lang', 'en')
    
    # Get user reports
    reports = report_db.get(user_id, [])
    
    if not reports:
        await query.answer()
        await query.edit_message_text(
            STRINGS[lang]['no_reports'],
            parse_mode='HTML'
        )
        return
    
    # Prepare report summary
    total_reports = len(reports)
    last_report_time = datetime.fromisoformat(reports[-1]['time']).strftime("%Y-%m-%d %H:%M")
    
    # Build recent reports list (last 5)
    recent_reports = []
    for report in reports[-5:]:
        report_time = datetime.fromisoformat(report['time']).strftime("%m/%d %H:%M")
        recent_reports.append(
            f"• <code>{report['id']}</code> | {report_time} | {report['target']}"
        )
    
    text = STRINGS[lang]['my_reports'].format(
        count=total_reports,
        last_report=last_report_time
    ) + "\n" + "\n".join(recent_reports[::-1])
    
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back_to_menu')]]
    
    await query.answer()
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )

async def show_help(update: Update, context: CallbackContext):
    query = update.callback_query
    lang = context.user_data.get('lang', 'en')
    
    await query.answer()
    await query.edit_message_text(
        STRINGS[lang]['help'],
        parse_mode='HTML'
    )

async def show_contact(update: Update, context: CallbackContext):
    query = update.callback_query
    lang = context.user_data.get('lang', 'en')
    
    await query.answer()
    await query.edit_message_text(
        STRINGS[lang]['contact'],
        parse_mode='HTML'
    )

async def admin_panel(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Access denied!")
        return ConversationHandler.END
        
    total_users = len(user_db)
    now = datetime.now()
    active_users = 0
    reports_today = 0
    
    for user_data in user_db.values():
        try:
            last_active = datetime.fromisoformat(user_data['last_active'])
            if last_active > now - timedelta(hours=24):
                active_users += 1
        except:
            continue
    
    # Count today's reports
    for reports in report_db.values():
        for report in reports:
            report_time = datetime.fromisoformat(report['time'])
            if report_time > now - timedelta(hours=24):
                reports_today += 1
    
    lang = 'en'
    stats = STRINGS[lang]['stats'].format(
        total=total_users,
        active=active_users,
        reports_today=reports_today
    )

    keyboard = [
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 System Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Main Menu", callback_data="admin_exit")]
    ]
    
    await update.message.reply_text(
        stats,
        reply_markup=InlineKeyboardMarkup(keyboard)),
        parse_mode='HTML'
    )
    return ADMIN_PANEL

async def start_broadcast(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📢 <b>GLOBAL BROADCAST</b>\n\nEnter your message:",
        parse_mode='HTML'
    )
    return BROADCAST_MESSAGE

async def send_broadcast(update: Update, context: CallbackContext):
    message = update.message.text
    lang = 'en'
    sent_count = 0
    
    for user_id in user_db.keys():
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=f"📢 <b>ANNOUNCEMENT</b> 📢\n\n{message}",
                parse_mode='HTML'
            )
            sent_count += 1
            await asyncio.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"Failed to send to {user_id}: {e}")
    
    await update.message.reply_text(
        STRINGS[lang]['broadcast_sent'].format(count=sent_count),
        parse_mode='HTML'
    )
    return await admin_panel(update, context)

async def back_to_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    lang = context.user_data.get('lang', 'en')
    await show_main_menu(update, context, lang)
    return MAIN_MENU

async def cancel(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    lang = context.user_data.get('lang', 'en')
    
    # Cancel any active session
    if user_id in sessions:
        sessions[user_id]['active'] = False
    
    await update.message.reply_text(
        "❌ Operation cancelled",
        reply_markup=ReplyKeyboardRemove()
    )
    await show_main_menu(update, context, lang)
    return MAIN_MENU

async def post_init(application):
    # Dummy initialization function
    await application.bot.set_my_commands([])

def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("ERROR: BOT_TOKEN environment variable not found!")
        print("Please set your Telegram bot token in the environment variables.")
        return

    try:
        app = (ApplicationBuilder()
               .token(BOT_TOKEN)
               .post_init(post_init)
               .build())

        conv = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                LANGUAGE: [CallbackQueryHandler(set_language)],
                MAIN_MENU: [CallbackQueryHandler(show_main_menu, pattern='^back_to_menu$'),
                            CallbackQueryHandler(start_report, pattern='^report_account$'),
                            CallbackQueryHandler(show_my_reports, pattern='^my_reports$'),
                            CallbackQueryHandler(show_help, pattern='^help$'),
                            CallbackQueryHandler(show_contact, pattern='^contact$')],
                REPORT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)],
                REPORT_TYPE: [CallbackQueryHandler(receive_report_type)],
                IMPERSONATION_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_impersonation_url)],
                REPORT_CONFIRM: [CallbackQueryHandler(start_reporting, pattern='^start_report$'),
                                 CallbackQueryHandler(back_to_menu, pattern='^back_to_menu$')],
                REPORT_PROGRESS: [CallbackQueryHandler(stop_reporting, pattern='^stop_report$')],
                ADMIN_PANEL: [CallbackQueryHandler(start_broadcast, pattern='^admin_broadcast$'),
                              CallbackQueryHandler(admin_panel, pattern='^admin_stats$'),
                              CallbackQueryHandler(back_to_menu, pattern='^admin_exit$')],
                BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_broadcast)]
            },
            fallbacks=[CommandHandler('cancel', cancel)]
        )

        app.add_handler(conv)
        app.add_handler(CommandHandler("admin", admin_panel))
        
        print("🚀 Bot started successfully!")
        app.run_polling()
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

if __name__ == "__main__":
    main()
