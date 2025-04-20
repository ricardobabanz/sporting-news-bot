import os
import asyncio
import logging
import feedparser
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# ───── Configuração ───────────────────────────────────────────────────────────

BOT_TOKEN = os.getenv("BOT_TOKEN")      # Variável de ambiente no Render
CHAT_ID   = os.getenv("CHAT_ID")        # Id do grupo, ex: -1001981830209

# Palavras‑chave (em minúsculas)
KEYWORDS = ["sporting", "leões", "alvalade", "leoes"]

# Lista completa de feeds RSS
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
    "https://maisfutebol.iol.pt/rss"  # se não houver, será ignorado
]

# Evitar duplicados
sent_links = set()

# Configurar logging
logging.basicConfig(
    format="%(asctime)s — %(levelname)s — %(message)s",
    level=logging.INFO
)

# ───── Funções ────────────────────────────────────────────────────────────────

async def send_news(context: ContextTypes.DEFAULT_TYPE):
    """Busca cada feed, filtra por KEYWORDS e envia para o grupo."""
    global sent_links

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            link  = entry.link
            title = entry.title
            lower = title.lower()

            # só processa se contiver keyword e não tiver sido enviado
            if link not in sent_links and any(k in lower for k in KEYWORDS):
                # descrição (summary ou description)
                description = entry.get("summary", entry.get("description", ""))
                
                # tentar tirar imagem og:image da própria página
                image_url = None
                try:
                    r = requests.get(link, timeout=5)
                    soup = BeautifulSoup(r.content, "html.parser")
                    img = soup.find("meta", property="og:image")
                    image_url = img["content"] if img else None
                except Exception as e:
                    logging.warning(f"Falha ao obter imagem de {link}: {e}")

                # montar mensagem
                caption = (
                    f"📰 <b>{title}</b>\n\n"
                    f"{description}\n\n"
                    f"<a href=\"{link}\">Ler no site</a>"
                )

                try:
                    if image_url:
                        await context.bot.send_photo(
                            chat_id=CHAT_ID,
                            photo=image_url,
                            caption=caption,
                            parse_mode=ParseMode.HTML
                        )
                    else:
                        await context.bot.send_message(
                            chat_id=CHAT_ID,
                            text=caption,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=False
                        )
                    sent_links.add(link)
                    logging.info(f"Enviado: {title}")
                except Exception as e:
                    logging.error(f"Erro ao enviar notícia: {e}")

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde ao /start."""
    await update.message.reply_text(
        "Olá! Estou ativo e a filtrar notícias do Sporting. 📡\n"
        "Usa /sporting para receber já as últimas."
    )

async def sporting_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde ao /sporting disparando uma busca imediata."""
    await send_news(context)

async def setup_jobs(app: ApplicationBuilder):
    """Configura o job para correr a cada 30 minutos."""
    app.job_queue.run_repeating(send_news, interval=1800, first=5)

# ───── Inicialização ─────────────────────────────────────────────────────────

async def main():
    # constrói a app e instala o JobQueue
    app = ApplicationBuilder() \
        .token(BOT_TOKEN) \
        .post_init(setup_jobs) \
        .build()

    # handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("sporting", sporting_cmd))

    # arranca
    await app.start()
    logging.info("Bot iniciado com sucesso!")
    await app.updater.start_polling()
    await app.idle()

if __name__ == "__main__":
    asyncio.run(main())
