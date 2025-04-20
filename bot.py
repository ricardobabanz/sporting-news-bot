import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import asyncio

TELEGRAM_TOKEN = '7795115723:AAFrAMolk2M2dzu1glrFSzrklR6t-caSmlg'
CHAT_ID = '-1001981830209'

RSS_FEEDS = [
    "https://www.abola.pt/rss/scp",
    "https://www.ojogo.pt/rss/sporting",
    "https://www.record.pt/rss/sporting",
    "https://www.fpf.pt/rss/atualidade",
    "https://www.sporting.pt/pt/noticias",
    "https://sicnoticias.pt/rss",
    "https://tvi.iol.pt/rss",
    "https://cnnportugal.iol.pt/rss",
    "https://www.flashscore.pt/rss",
    "https://www.zerozero.pt/rss",
    "https://www.rtp.pt/rss",
    "https://maisfutebol.iol.pt/rss"
]

last_titles = set()

logging.basicConfig(level=logging.INFO)

async def send_news(context: ContextTypes.DEFAULT_TYPE):
    global last_titles

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            if entry.title not in last_titles:
                last_titles.add(entry.title)

                # Tentar obter imagem da descrição (se existir)
                soup = BeautifulSoup(entry.get("summary", ""), "html.parser")
                img_tag = soup.find("img")
                image_url = img_tag["src"] if img_tag else None

                message = f"*{entry.title}*\n\n{entry.get('summary', '')}\n\n[Link]({entry.link})"

                try:
                    if image_url:
                        await context.bot.send_photo(
                            chat_id=CHAT_ID,
                            photo=image_url,
                            caption=entry.title,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=CHAT_ID,
                            text=message,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=False
                        )
                except Exception as e:
                    logging.error(f"Erro ao enviar mensagem: {e}")

async def start(update, context):
    await update.message.reply_text("Bot está ativo!")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Envia notícias a cada 30 minutos
    app.job_queue.run_repeating(send_news, interval=1800, first=5)

    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
