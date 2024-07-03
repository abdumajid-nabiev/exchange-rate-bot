import requests
from datetime import datetime, time
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, CallbackContext, Application, CallbackContext, ContextTypes

# Replace with your Telegram bot token and chat ID
BOT_TOKEN = '1974949313:AAGAqJpXAz7CRueHjdRiObjZ_-3W23VY5do'
CHAT_ID = '1001861433470'  # Replace with your chat ID

# Function to fetch exchange rates from the Central Bank of Uzbekistan's API
def fetch_exchange_rates():
    url = "https://cbu.uz/uzc/arkhiv-kursov-valyut/json/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        rates = {item['Ccy']: float(item['Rate']) for item in data}
        return rates
    else:
        print("Error fetching rates:", response.status_code, response.text)
        return None

# Function to send daily exchange rates
async def send_daily_rates(context: CallbackContext):
    rates = fetch_exchange_rates()
    if rates:
        message = f"""
🇺🇿  Markaziy Bank sanasi: {datetime.now().strftime('%d.%m.%Y')}
1 🇺🇸 Dollar = {rates['USD']:.2f} UZS
1 🇪🇺 Yevro = {rates['EUR']:.2f} UZS
1 🇬🇧 Funt = {rates['GBP']:.2f} UZS
1 🇷🇺 Rubl = {rates['RUB']:.2f} UZS
1 🇨🇳 Yuan = {rates['CNY']:.2f} UZS
1 🇰🇷 Von = {rates['KRW']:.2f} UZS
1 🇹🇷 Lira = {rates['TRY']:.2f} UZS
1 🇹🇲 Manat = {rates['TMT']:.2f} UZS
1 🇰🇿 Tenge = {rates['KZT']:.2f} UZS
1 🇹🇯 Somoni = {rates['TJS']:.2f} UZS
1 🇰🇬 Som = {rates['KGS']:.2f} UZS
1 🇦🇪 Dirham = {rates['AED']:.2f} UZS

✅ @NimaUchun_N1 - Obuna bo‘ling!
        """
        await context.bot.send_message(chat_id=CHAT_ID, text=message)
    else:
        await context.bot.send_message(chat_id=CHAT_ID, text="Error fetching exchange rates.")

# Command handler for /rates to check exchange rates on demand
async def check_rates(update: Update, context: CallbackContext):
    rates = fetch_exchange_rates()
    if rates:
        message = f"""
🇺🇿  Markaziy Bank sanasi: {datetime.now().strftime('%d.%m.%Y')}
1 🇺🇸 Dollar = {rates['USD']:.2f} UZS
1 🇪🇺 Yevro = {rates['EUR']:.2f} UZS
1 🇬🇧 Funt = {rates['GBP']:.2f} UZS
1 🇷🇺 Rubl = {rates['RUB']:.2f} UZS
1 🇨🇳 Yuan = {rates['CNY']:.2f} UZS
1 🇰🇷 Von = {rates['KRW']:.2f} UZS
1 🇹🇷 Lira = {rates['TRY']:.2f} UZS
1 🇹🇲 Manat = {rates['TMT']:.2f} UZS
1 🇰🇿 Tenge = {rates['KZT']:.2f} UZS
1 🇹🇯 Somoni = {rates['TJS']:.2f} UZS
1 🇰🇬 Som = {rates['KGS']:.2f} UZS
1 🇦🇪 Dirham = {rates['AED']:.2f} UZS
        """
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Error fetching exchange rates.")

# Main function to initialize the bot
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Schedule the job to run daily at 06:00 AM in Tashkent time
    job_queue = application.job_queue
    job_queue.run_daily(send_daily_rates, time=time(hour=6, minute=0, second=0))

    # Add command handlers
    application.add_handler(CommandHandler('rates', check_rates))

    application.run_polling()

if __name__ == '__main__':
    main()
