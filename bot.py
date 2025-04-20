import feedparser
import requests
from bs4 import BeautifulSoup
import time
from telegram import Bot
from telegram.ext import Updater, CommandHandler
import os

# Variáveis de ambiente
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GROUP_ID = os.getenv('GROUP_ID')

# Lista de feeds RSS
rss_feeds = [
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
]

# Função para buscar as notícias
def get_sporting_news():
    news_list = []
    for feed_url in rss_feeds:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            if "Sporting" in entry.title:
                news_list.append({
                    'title': entry.title,
                    'link': entry.link,
                    'description': entry.description,
                    'published': entry.published,
                    'image': get_image_from_url(entry.link)
                })
    return news_list

# Função para extrair imagem da página (usando BeautifulSoup)
def get_image_from_url(url):
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        image = soup.find('meta', property='og:image')
        return image['content'] if image else None
    except Exception as e:
        return None

# Enviar notícia para o grupo no Telegram
def send_news(update, context):
    news_list = get_sporting_news()
    for news in news_list:
        title = news['title']
        description = news['description']
        link = news['link']
        image = news['image']

        message = f"📰 *{title}*\n\n{description}\n\n🔗 {link}"
        if image:
            context.bot.send_photo(chat_id=GROUP_ID, photo=image, caption=message)
        else:
            context.bot.send_message(chat_id=GROUP_ID, text=message)

# Comando /sporting
def start(update, context):
    send_news(update, context)

# Função principal do bot
def main():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Comando /sporting
    dp.add_handler(CommandHandler("sporting", start))

    # Start the bot
    updater.start_polling()
    updater.idle()

# Para correr o bot a cada 30 minutos
if __name__ == '__main__':
    while True:
        main()
        time.sleep(1800)  # 30 minutos
