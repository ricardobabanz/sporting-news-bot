import os
import logging
import feedparser
from bs4 import BeautifulSoup
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ───── Configuração ───────────────────────────────────────────────────────────

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")

KEYWORDS = ["sporting", "leões", "alvalade", "leoes"]

RSS_FEEDS = [
    "https://www.abola.pt/rss/scp",
    "https://www.ojogo.pt/rss/sporting",
    "https://www.record.pt/rss/sporting",
    "https://www.fpf.pt/rss/atualidade",
    "https://sicnoticias.pt/rss",
    "https://tvi.iol.pt/rss",
    "https://cnnportugal.iol.pt/rss",
    "https://www.flashscore.pt/rss",
    "https://www.zerozero.pt/rss",
    "https://www.rtp.pt/rss",
    "https://www.sporting.pt/pt/rss/noticias.xml",
    "https://maisfutebol.iol.pt/rss"
]

sent_links = set()

logging.basicConfig(
    format="%(asctime)s — %(levelname)s — %(message)s",
    level=logging.INFO
)

# ───── Funções ────────────────────────────────────────────────────────────────

async def send_news(context: ContextTypes.DEFAULT_TYPE):
    global sent_links
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            link  = entry.link
            title = entry.title
            lower = title.lower()

            if link not in sent_links and any(k in lower for k in KEYWORDS):
                # limpa HTML do resumo
                raw_desc   = entry.get("summary", entry.get("description", ""))
                description = BeautifulSoup(raw_desc, "html.parser").get_text()

                # monta a mensagem só com texto
                caption = (
                    f"📰 <b>{title}</b>\n\n"
                    f"{description}\n\n"
                    f"<a href=\"{link}\">Ler no site</a>"
                )

                try:
                    await context.bot.send_message(
                        chat_id=CHAT_ID,
                        text=caption,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=False
                    )
                    sent_links.add(link)
                    logging.info(f"Enviado: {title}")
                except Exception as e:
                    logging.error(f"Falha ao enviar notícia: {e}")

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Estou ativo e filtrando notícias do Sporting. 🦁\n"
        "Use /sporting para receber agora as últimas."
    )

async def sporting_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_news(context)

async def setup_jobs(app):
    app.job_queue.run_repeating(send_news, interval=1800, first=5)

# ───── Inicialização ─────────────────────────────────────────────────────────

def main():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(setup_jobs)
        .build()
    )

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("sporting", sporting_cmd))

    logging.info("Bot do Sporting iniciado. A correr polling…")
    app.run_polling()

if __name__ == "__main__":
    main()
