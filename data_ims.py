import pandas as pd
import json
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, Document
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler
)

# CONFIG
BOT_TOKEN = '7784941170:AAGiwRyxa6lDYYkouf9gdjUyt9203vz0Kjo'
ADMIN_ID = 7730908928  # Replace with your Telegram ID
EXCEL_FILE = "faculty.xlsx"
AUTHORIZED_FILE = "authorized_users.json"

# GLOBAL DATA
df = pd.DataFrame()

# Load authorized users
def load_authorized_users():
    try:
        with open(AUTHORIZED_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_authorized_users(users):
    with open(AUTHORIZED_FILE, 'w') as f:
        json.dump(users, f)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    authorized = load_authorized_users()

    if user_id in authorized or user_id == ADMIN_ID:
        await update.message.reply_text("Welcome! Use /search <name> to look up data.")
    else:
        await update.message.reply_text("Access denied. Request sent to admin for approval.")

        # Send request to admin
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
             InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")]
        ])
        msg = f"New user wants access:\nName: {update.message.from_user.full_name}\nUsername: @{update.message.from_user.username}\nID: {user_id}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg, reply_markup=keyboard)

# Button clicks (approve/reject)
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Answer the callback query to avoid timeout issue

    data = query.data
    print(f"Callback Data: {data}")  # Debugging line to check data

    if data.startswith("approve_"):
        uid = int(data.split("_")[1])  # Extract user ID after 'approve_'
        print(f"Approving User ID: {uid}")  # Debugging line to check user ID
        users = load_authorized_users()
        if uid not in users:
            users.append(uid)
            save_authorized_users(users)  # Save the updated list of users
            await context.bot.send_message(chat_id=uid, text="Access mil gya h madrrchod . abb use krr le .")  # Notify user
        await query.edit_message_text("User approved.")  # Notify admin that the user was approved

    elif data.startswith("reject_"):
        uid = int(data.split("_")[1])  # Extract user ID after 'reject_'
        print(f"Rejecting User ID: {uid}")  # Debugging line to check user ID
        await context.bot.send_message(chat_id=uid, text="Access denied by admin.")  # Notify user
        await query.edit_message_text("User rejected.")  # Notify admin that the user was rejected

# /search <name>
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    user_id = update.message.from_user.id
    if user_id not in load_authorized_users() and user_id != ADMIN_ID:
        await update.message.reply_text("Unauthorized. Request access using /start.")
        return

    if df.empty:
        await update.message.reply_text("No Excel file loaded yet.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /search <name>")
        return

    name = " ".join(context.args).lower()
    matches = df[df['Name'].fillna('').str.lower().str.contains(name)]  # Search for name in the 'Name' column

    if matches.empty:
        await update.message.reply_text("No matching records found.")
    else:
        response = ""
        for _, row in matches.iterrows():
            for col, val in row.items():
                response += f"{col}: {val}\n"
        response += "\n"
        await update.message.reply_text(response.strip())

# Excel upload (admin-only)
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    user = update.message.from_user
    if user.id != ADMIN_ID:
        await update.message.reply_text("Only admin can upload Excel.")
        return

    doc: Document = update.message.document
    if not doc.file_name.endswith(".xlsx"):
        await update.message.reply_text("Upload a valid .xlsx file.")
        return

    file_path = f"temp_{doc.file_name}"
    file = await doc.get_file()
    await file.download_to_drive(file_path)

    try:
        df = pd.read_excel(file_path)
        await update.message.reply_text("Excel loaded successfully.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

# MAIN
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    print("Bot running...")
    app.run_polling()
