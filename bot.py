
import requests
from datetime import datetime, time
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackContext, JobQueue, Updater

# Replace with your Telegram bot token and exchange rate API key
BOT_TOKEN = '1974949313:AAGAqJpXAz7CRueHjdRiObjZ_-3W23VY5do'
API_KEY = '4019492e95e85e1e297a06ed'
CHAT_ID = '1001861433470'  # Replace with your chat ID


# Function to fetch exchange rates
def fetch_exchange_rates():
    url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/UZS"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print("Error fetching rates:", response.status_code, response.text)
        return None

# Function to convert and format the exchange rates
def format_rates(rates):
    conversion_rates = {
        'USD': ('🇺🇸 Dollar', rates['conversion_rates'].get('USD', 1)),
        'EUR': ('🇪🇺 Yevro', rates['conversion_rates'].get('EUR', 1)),
        'GBP': ('🇬🇧 Funt', rates['conversion_rates'].get('GBP', 1)),
        'RUB': ('🇷🇺 Rubl', rates['conversion_rates'].get('RUB', 1)),
        'CNY': ('🇨🇳 Yuan', rates['conversion_rates'].get('CNY', 1)),
        'KRW': ('🇰🇷 Von', rates['conversion_rates'].get('KRW', 1)),
        'TRY': ('🇹🇷 Lira', rates['conversion_rates'].get('TRY', 1)),
        'TMT': ('🇹🇲 Manat', rates['conversion_rates'].get('TMT', 1)),
        'KZT': ('🇰🇿 Tenge', rates['conversion_rates'].get('KZT', 1)),
        'TJS': ('🇹🇯 Somoni', rates['conversion_rates'].get('TJS', 1)),
        'KGS': ('🇰🇬 Som', rates['conversion_rates'].get('KGS', 1)),
        'AED': ('🇦🇪 Dirham', rates['conversion_rates'].get('AED', 1))
    }

    formatted_message = f"🇺🇿  Markaziy Bank sanasi: {datetime.now().strftime('%d.%m.%Y')}\n"
    for currency, (name, rate) in conversion_rates.items():
        uzs_rate = 1 / rate
        formatted_message += f"1 {name} = {uzs_rate:,.2f} UZS\n"

    formatted_message += "\n✅ @NimaUchun_N1 - Obuna bo‘ling!"
    return formatted_message

# Function to send daily exchange rates
async def send_daily_rates(context: CallbackContext):
    rates = fetch_exchange_rates()
    if rates:
        message = format_rates(rates)
        await context.bot.send_message(chat_id=CHAT_ID, text=message)
    else:
        await context.bot.send_message(chat_id=CHAT_ID, text="Error fetching exchange rates.")

# Command handler for /rates to check exchange rates on demand
async def check_rates(update: Update, context: CallbackContext):
    rates = fetch_exchange_rates()
    if rates:
        message = format_rates(rates)
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Error fetching exchange rates.")

# Main function to initialize the bot
def main():
    application = Application.builder().token(BOT_TOKEN).build()
    job_queue = application.job_queue

    # Schedule the job to run daily at 06:00 AM in Tashkent time
    job_queue.run_daily(send_daily_rates, time=time(hour=6, minute=0, second=0))

    # Add command handlers
    application.add_handler(CommandHandler('rates', check_rates))

    application.run_polling()

if __name__ == '__main__':
    main()

