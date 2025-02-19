from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import logging
import asyncio
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext

app = Flask(__name__)

# Load dataset from CSV
try:
    csv_path = os.path.join(os.path.dirname(__file__), 'sample_updated.csv')
    df = pd.read_csv(csv_path)
except FileNotFoundError:
    print("Error: CSV file not found. Please check the file path.")
    exit()

df = df.sort_values('gameNumber', ascending=False).reset_index(drop=True)
df['type'] = df['type'].str.lower()

# Function to find pattern probability
def find_pattern_probability(pattern):
    sizes = df['type'].tolist()
    pattern_occurrences = 0
    next_small_count = 0
    next_big_count = 0
    
    pattern = ['small' if p == 's' else 'big' for p in pattern]
    for i in range(len(sizes) - len(pattern)):
        if all(sizes[i + j] == pattern[j] for j in range(len(pattern))):
            pattern_occurrences += 1
            next_index = i + len(pattern)
            if next_index < len(sizes):
                next_value = sizes[next_index]
                if next_value == 'small':
                    next_small_count += 1
                elif next_value == 'big':
                    next_big_count += 1
    
    if pattern_occurrences > 0:
        small_probability = next_small_count / pattern_occurrences
        big_probability = next_big_count / pattern_occurrences
    else:
        small_probability = big_probability = 0
    
    return {
        'small_probability': small_probability,
        'big_probability': big_probability,
        'pattern_occurrences': pattern_occurrences
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    input_pattern = request.form['pattern'].lower().strip().split(',')
    analysis_results = find_pattern_probability(input_pattern)
    return jsonify(analysis_results)

# Telegram Bot Setup
TOKEN = "7822711424:AAFN2RDVmWisSHhMLHsQt8iD1tkTY84YqUk"
CHAT_ID = -1002496564742
last_message = {"text": "No messages yet", "sender": "Unknown"}
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: CallbackContext):
    global last_message
    message = update.effective_message
    if message:
        last_message["text"] = message.text or "[Non-text message]"
        last_message["sender"] = message.chat.username or message.chat.title or "Unknown"
        logger.info(f"New Message from {last_message['sender']}: {last_message['text']}")

async def start_bot():
    bot_app = Application.builder().token(TOKEN).build()
    bot_app.add_handler(MessageHandler(filters.Chat(CHAT_ID), handle_message))
    logger.info("Bot started... Listening for new messages...")
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.run_polling()

@app.route('/last_message', methods=['GET'])
def get_last_message():
    return jsonify(last_message)

def run_bot():
    asyncio.run(start_bot())

if __name__ == '__main__':
    # Start Telegram bot in a separate thread
    bot_thread = Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
