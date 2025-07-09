import os
import sqlite3
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import requests
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, ContextTypes
)
from dotenv import load_dotenv
from telegram.ext import Application, AIORateLimiter

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN") or "1974949313:AAGAqJpXAz7CRueHjdRiObjZ_-3W23VY5do"
CHAT_ID = os.getenv("CHAT_ID") or "-1001861433470"
ADMIN_ID = 691728393  # Your Telegram user ID

DB_PATH = "rates.db"
flags_dir = "flags"

# Map currency codes to country codes for flags
currency_to_country = {
    "USD": "us",
    "EUR": "eu",
    "GBP": "gb",
    "RUB": "ru",
    "CNY": "cn",
    "KRW": "kr",
    "TRY": "tr",
    "TMT": "tm",
    "KZT": "kz",
    "TJS": "tj",
    "KGS": "kg",
    "AED": "ae",
}


async def after_startup(app):
    print("Bot has started.")

# --- Fetching Exchange Rates --- #
def fetch_exchange_rates():
    url = "https://cbu.uz/uzc/arkhiv-kursov-valyut/json/"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        rates = {item['Ccy']: float(item['Rate']) for item in data}
        return rates
    except requests.RequestException as e:
        print("Error fetching rates:", e)
        return None


# --- Store to SQLite --- #
def store_rates(rates: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS rates (
            date TEXT, ccy TEXT, rate REAL,
            PRIMARY KEY (date, ccy)
        )
    """)
    today = datetime.now(ZoneInfo("Asia/Tashkent")).date().isoformat()
    for ccy, rate in rates.items():
        c.execute("REPLACE INTO rates (date, ccy, rate) VALUES (?, ?, ?)", (today, ccy, rate))
    conn.commit()
    conn.close()


# --- Load History --- #
def load_rate_history(ccy_list: list[str], days: int = 7):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    since = (datetime.now(ZoneInfo("Asia/Tashkent")) - timedelta(days=days)).date().isoformat()
    data_dict = {}
    for ccy in ccy_list:
        c.execute("SELECT date, rate FROM rates WHERE ccy = ? AND date >= ? ORDER BY date", (ccy, since))
        data = c.fetchall()
        data_dict[ccy] = data
    conn.close()
    return data_dict


# --- Generate Weekly Bar Chart (7-day trend) --- #
def generate_weekly_bar_chart(data_dict: dict[str, list[tuple[str, float]]]):
    dates = sorted(list(set(date for data in data_dict.values() for date, _ in data)))
    currency_list = list(data_dict.keys())
    date_indices = {date: idx for idx, date in enumerate(dates)}

    width = 0.08
    x = range(len(dates))
    plt.figure(figsize=(12, 6))

    for i, ccy in enumerate(currency_list):
        values = [0] * len(dates)
        for date, rate in data_dict[ccy]:
            values[date_indices[date]] = rate
        positions = [xi + i * width for xi in x]
        plt.bar(positions, values, width=width, label=ccy)

    plt.xticks([xi + width * len(currency_list) / 2 for xi in x], dates, rotation=45)
    plt.xlabel("Sana")
    plt.ylabel("UZS")
    plt.title("Oxirgi 7 kunlik valyuta kurslari")
    plt.legend()
    plt.tight_layout()

    filename = "weekly_bar_chart.png"
    plt.savefig(filename)
    plt.close()
    return filename


from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.image as mpimg
import os

def generate_currency_ranking_chart(rates: dict, ccy_list: list[str], currency_names: dict[str, str], flags_dir="flags"):
    values = [rates.get(ccy, 0) for ccy in ccy_list]
    labels = [currency_names.get(ccy, ccy) for ccy in ccy_list]

    # Sort by value descending
    sorted_data = sorted(zip(values, labels, ccy_list), reverse=True)
    sorted_values, sorted_labels, sorted_ccys = zip(*sorted_data)

    fig, ax = plt.subplots(figsize=(12, 7))

    # Use tab20 color palette for distinct colors
    colors = plt.get_cmap('tab20').colors
    bar_colors = [colors[i % len(colors)] for i in range(len(sorted_ccys))]

    bars = ax.barh(sorted_labels, sorted_values, color=bar_colors)
    ax.set_xlabel("UZS")
    ax.set_title("💰 Bugungi valyuta kurslari (To‘liq ma’lumot bilan)")

    max_value = max(sorted_values)
    left_margin = max_value * 0.15  # increased margin for larger flags
    ax.set_xlim(left=-left_margin, right=max_value * 1.15)

    for i, (bar, value, ccy) in enumerate(zip(bars, sorted_values, sorted_ccys)):
        y = bar.get_y() + bar.get_height() / 2

        # Map currency code to country code
        country_code = currency_to_country.get(ccy.upper())
        if country_code:
            flag_path = os.path.join(flags_dir, f"{country_code.lower()}.png")
        else:
            flag_path = None

        # Add flag with robust error handling
        if flag_path and os.path.isfile(flag_path):
            try:
                img = mpimg.imread(flag_path)
                # Flag size: zoom adjusted for visibility and consistent size
                zoom = 0.23  
                imagebox = OffsetImage(img, zoom=zoom)
                # Position flags to the left, vertically centered on bar
                ab = AnnotationBbox(imagebox, (-left_margin * 0.3, y),
                                    frameon=False, box_alignment=(0.3, 0.3))
                ax.add_artist(ab)
            except Exception as e:
                print(f"Error loading flag for {ccy}: {e}")

        # Show value label:
        # If bar is long enough to fit label inside right edge, show inside in white bold text
        # Else show label outside to the right in default color
        if value > max_value * 1.50:
             ax.text(value - max_value * 0.10, y, f"{value:,.2f} UZS",
            va='center', ha='right', fontsize=13, color='white', fontweight='bold')
        else:
            ax.text(value + max_value * 0.01, y, f"{value:,.2f} UZS",
            va='center', ha='left', fontsize=10)


    ax.invert_yaxis()  # Highest value on top
    plt.tight_layout()
    filename = "currency_ranking_detailed_chart.png"
    plt.savefig(filename)
    plt.close()
    return filename



# --- Format Message --- #
def format_rates_message(rates: dict) -> str:
    lines = [f"🇺🇿  Markaziy Bank sanasi: {datetime.now(ZoneInfo('Asia/Tashkent')).strftime('%d.%m.%Y')}"]
    currency_map = {
        "USD": "🇺🇸 Dollar", "EUR": "🇪🇺 Yevro", "GBP": "🇬🇧 Funt", "RUB": "🇷🇺 Rubl",
        "CNY": "🇨🇳 Yuan", "KRW": "🇰🇷 Von", "TRY": "🇹🇷 Lira", "TMT": "🇹🇲 Manat",
        "KZT": "🇰🇿 Tenge", "TJS": "🇹🇯 Somoni", "KGS": "🇰🇬 Som", "AED": "🇦🇪 Dirham"
    }
    for code, name in currency_map.items():
        rate = rates.get(code, 0)
        lines.append(f"1 {name} = {rate:.2f} UZS")
    lines.append("\n🌟 @markaziy_bank_rates - Obuna bo‘ling!")
    return "\n".join(lines)


# --- Send Daily Message & Chart --- #
async def send_daily_rates(context: ContextTypes.DEFAULT_TYPE):
    rates = fetch_exchange_rates()
    if not rates:
        await context.bot.send_message(chat_id=CHAT_ID, text="❌ Valyuta kurslarini olishda xatolik yuz berdi.")
        return

    store_rates(rates)
    message = format_rates_message(rates)

    ccy_list = list(currency_to_country.keys())
    currency_names = {
        "USD": "🇺🇸 Dollar", "EUR": "🇪🇺 Yevro", "GBP": "🇬🇧 Funt", "RUB": "🇷🇺 Rubl",
        "CNY": "🇨🇳 Yuan", "KRW": "🇰🇷 Von", "TRY": "🇹🇷 Lira", "TMT": "🇹🇲 Manat",
        "KZT": "🇰🇿 Tenge", "TJS": "🇹🇯 Somoni", "KGS": "🇰🇬 Som", "AED": "🇦🇪 Dirham"
    }

    image_path = generate_currency_ranking_chart(rates, ccy_list, currency_names)

    with open(image_path, 'rb') as photo:
        await context.bot.send_photo(chat_id=CHAT_ID, photo=photo, caption=message)


# --- Command Handler (/rates) --- #
async def check_rates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rates = fetch_exchange_rates()
    if not rates:
        await update.message.reply_text("❌ Valyuta kurslarini olishda xatolik yuz berdi.")
        return

    store_rates(rates)
    message = format_rates_message(rates)

    ccy_list = list(currency_to_country.keys())
    currency_names = {
        "USD": "🇺🇸 Dollar",
        "EUR": "🇪🇺 Yevro",
        "GBP": "🇬🇧 Funt",
        "RUB": "🇷🇺 Rubl",
        "CNY": "🇨🇳 Yuan",
        "KRW": "🇰🇷 Von",
        "TRY": "🇹🇷 Lira",
        "TMT": "🇹🇲 Manat",
        "KZT": "🇰🇿 Tenge",
        "TJS": "🇹🇯 Somoni",
        "KGS": "🇰🇬 Som",
        "AED": "🇦🇪 Dirham"
    }
    image_path = generate_currency_ranking_chart(rates, ccy_list, currency_names)

    with open(image_path, 'rb') as photo:
        await update.message.reply_photo(photo=photo, caption=message)


async def send_rates_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Sizda bu buyruqni ishlatishga ruxsat yo‘q.")
        return

    rates = fetch_exchange_rates()
    if not rates:
        await update.message.reply_text("❌ Valyuta kurslarini olishda xatolik yuz berdi.")
        return

    store_rates(rates)
    message = format_rates_message(rates)

    ccy_list = ["USD", "EUR", "GBP", "RUB", "CNY", "KRW", "TRY", "TMT", "KZT", "TJS", "KGS", "AED"]
    currency_names = {
        "USD": "🇺🇸 Dollar", "EUR": "🇪🇺 Yevro", "GBP": "🇬🇧 Funt", "RUB": "🇷🇺 Rubl",
        "CNY": "🇨🇳 Yuan", "KRW": "🇰🇷 Von", "TRY": "🇹🇷 Lira", "TMT": "🇹🇲 Manat",
        "KZT": "🇰🇿 Tenge", "TJS": "🇹🇯 Somoni", "KGS": "🇰🇬 Som", "AED": "🇦🇪 Dirham"
    }

    image_path = generate_currency_ranking_chart(rates, ccy_list, currency_names)

    try:
        await context.bot.send_photo(chat_id=CHAT_ID, photo=open(image_path, 'rb'), caption=message)
        await update.message.reply_text("✅ Kurslar kanalga yuborildi.")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")

def store_rates(rates: dict):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS rates (
            date TEXT, ccy TEXT, rate REAL,
            PRIMARY KEY (date, ccy)
        )
    """)
    today = datetime.now(ZoneInfo("Asia/Tashkent")).date().isoformat()
    for ccy, rate in rates.items():
        c.execute("REPLACE INTO rates (date, ccy, rate) VALUES (?, ?, ?)", (today, ccy, rate))

    # 🔥 Cleanup old records older than 30 days (safe)
    cutoff = (datetime.now(ZoneInfo("Asia/Tashkent")) - timedelta(days=30)).date().isoformat()
    c.execute("DELETE FROM rates WHERE date < ?", (cutoff,))

    conn.commit()
    conn.close()



# --- Main Entry --- #
def main():
    application = (
    Application.builder()
    .token(BOT_TOKEN)
    .rate_limiter(AIORateLimiter())
    .post_init(after_startup)
    .build()
)
    application.job_queue.run_daily(
    send_daily_rates,
    time=time(hour=5, minute=0, second=0, tzinfo=ZoneInfo("Asia/Tashkent"))
)
    application.add_handler(CommandHandler("rates", check_rates))
    application.add_handler(CommandHandler("send_rates", send_rates_to_channel))
    application.run_polling()


if __name__ == '__main__':
    main()
