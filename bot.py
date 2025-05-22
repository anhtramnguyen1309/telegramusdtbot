import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
# Token bot Telegram (sửa trực tiếp ở đây nếu không dùng biến môi trường)
TOKEN = "7929848191:AAGX4CUXNAABjOGU9nh1HggVguOURt0FDTA"

# Lấy giá mua USDT trên Binance P2P (VNĐ)
def get_binance_p2p_buy_price():
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    headers = { "Content-Type": "application/json" }
    payload = {
    "page": 1,
    "rows": 10,
    "asset": "USDT",
    "tradeType": "BUY",
    "fiat": "VND",
    "payTypes": ["BANK"],
    "publisherType": None,
    "transAmount": "500000000"  # lọc đúng mức giới hạn giống app
}

    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        print("Kết quả Binance P2P:", data)  # In ra để debug

        if 'data' in data and data['data']:
            prices = [float(ad['adv']['price']) for ad in data['data']if float(ad['adv']['price'])>00]
            if prices:
                return min(prices)
        return None
    except Exception as e:
        print("Lỗi lấy giá Binance P2P:", e)
        return None

# Lấy giá USDT từ sàn Bithumb (USDT/KRW)
def get_bithumb_price():
    try:
        response = requests.get("https://api.bithumb.com/public/ticker/USDT_KRW")
        data = response.json()
        if data['status'] == '0000':
            return float(data['data']['closing_price'])
        return None
    except Exception as e:
        print("Lỗi lấy giá Bithumb:", e)
        return None

# Lệnh /price: gửi giá ngay
async def send_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    binance_price = get_binance_p2p_buy_price()
    bithumb_price = get_bithumb_price() 
    if binance_price and bithumb_price:
       ratio = binance_price / bithumb_price
       msg = (
           f"Binance P2P: {binance_price:,.0f} VND\n"
           f"Bithumb: {bithumb_price:,.0f} KRW\n"
           f"krw rate: {ratio:.3f} VND/KRW"
       )
    else:
       msg = "Không lấy được dữ liệu giá."
      
    await update.message.reply_text(msg) 

# Gửi giá định kỳ mỗi giờ
async def scheduled_send(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    binance_price = get_binance_p2p_buy_price()
    bithumb_price = get_bithumb_price() 
    msg = "Không lấy được dữ liệu giá."
    if binance_price and bithumb_price:
        msg = (
            f"💵 Binance P2P: {binance_price:,.0f} VND\n"
            f"💱 Bithumb: {bithumb_price:,.0f} KRW"
        )
        await context.bot.send_message(chat_id=chat_id, text=msg)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Không lấy được dữ liệu giá.")

# Lệnh /start: bắt đầu theo dõi giá mỗi giờ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.job_queue.run_repeating(scheduled_send, interval=3600, first=0, chat_id=update.effective_chat.id)
    await update.message.reply_text("Bot đã bắt đầu theo dõi giá mỗi giờ.")

# Khởi chạy bot
if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    async def init_job_queue(app):
        app.job_queue

    app = ApplicationBuilder().token(TOKEN).post_init(init_job_queue).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("price", send_price))
    print("✅ Bot đang chạy...")
    app.run_polling()