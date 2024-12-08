import requests
import time
from bs4 import BeautifulSoup
from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext

# Replace these with your actual bot token and group IDs
BOT_TOKEN = "7215448892:AAFfMvaXe1j8PUrrfdRvN9XHZpPHlAjOBxk"
HIGH_QUALITY_GROUP = -1002377251885  # Replace with your High-quality group ID
MEDIUM_QUALITY_GROUP = -1002295649275  # Replace with your Medium-quality group ID
LOW_QUALITY_GROUP = -1002299532202  # Replace with your Low-quality group ID

PROXY_SOURCES = [
    "https://www.freeproxylists.net/",
    "https://www.sslproxies.org/",
    "https://free-proxy-list.net/",
    "https://proxy-daily.com/",
    "https://www.us-proxy.org/",
    "https://www.socks-proxy.net/",
    "https://www.proxynova.com/proxy-server-list/",
    "https://hidemy.name/en/proxy-list/"
]

def scrape_proxies():
    proxies = []
    try:
        url = "https://www.freeproxylists.net/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                ip = cols[0].text.strip()
                port = cols[1].text.strip()
                country = cols[2].text.strip()
                proxy_type = "HTTP"
                proxies.append({"ip": ip, "port": port, "type": proxy_type, "country": country})
    except Exception as e:
        print(f"Error scraping from Free Proxy Lists: {e}")
# Parse SSL Proxies
    try:
        url = "https://www.sslproxies.org/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table tbody tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 3:
                ip = cols[0].text.strip()
                port = cols[1].text.strip()
                country = cols[3].text.strip()  # Assuming the 4th column is Country
                proxy_type = "HTTP/HTTPS"
                proxies.append({"ip": ip, "port": port, "type": proxy_type, "country": country})
    except Exception as e:
        print(f"Error scraping from SSL Proxies: {e}")

    # Parse Proxy Daily
    try:
        url = "https://proxy-daily.com/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        proxy_blocks = soup.find_all("div", class_="centeredProxyList freeProxyStyle")
        for block in proxy_blocks:
            proxy_lines = block.text.strip().split("\n")
            for line in proxy_lines:
                if ":" in line:
                    ip, port = line.split(":")
                    proxies.append({"ip": ip.strip(), "port": port.strip(), "type": "HTTP", "country": "Unknown"})
    except Exception as e:
        print(f"Error scraping from Proxy Daily: {e}")

    return proxies

def test_proxy_latency(proxy):
    try:
        start = time.time()
        response = requests.get("https://httpbin.org/ip", proxies={"http": f"http://{proxy['ip']}:{proxy['port']}"}, timeout=5)
        if response.status_code == 200:
            latency = time.time() - start
            return latency
    except:
        return float('inf')  # Treat unresponsive proxies as having infinite latency
    return float('inf')

def categorize_proxies(proxies):
    high_quality = []
    medium_quality = []
    low_quality = []

    for proxy in proxies:
        latency = test_proxy_latency(proxy)
        formatted_proxy = f"{proxy['ip']}:{proxy['port']} | Type: {proxy['type']} | Country: {proxy['country']} | Latency: {latency:.2f}s"
        if latency < 0.5:  # Less than 500 ms
            high_quality.append(formatted_proxy)
        elif 0.5 <= latency <= 1.5:  # Between 500 ms and 1500 ms
            medium_quality.append(formatted_proxy)
        else:  # Greater than 1500 ms
            low_quality.append(formatted_proxy)

    return high_quality, medium_quality, low_quality

def distribute_proxies(context: CallbackContext):
    proxies = scrape_proxies()
    if not proxies:
        print("No proxies found.")
        return

    high_quality, medium_quality, low_quality = categorize_proxies(proxies)

    if high_quality:
        context.bot.send_message(
            HIGH_QUALITY_GROUP,
            f"High Quality Proxies:\n```{chr(10).join(high_quality)}```",
            parse_mode=ParseMode.MARKDOWN
        )
    if medium_quality:
        context.bot.send_message(
            MEDIUM_QUALITY_GROUP,
            f"Medium Quality Proxies:\n```{chr(10).join(medium_quality)}```",
            parse_mode=ParseMode.MARKDOWN
        )
    if low_quality:
        context.bot.send_message(
            LOW_QUALITY_GROUP,
            f"Low Quality Proxies:\n```{chr(10).join(low_quality)}```",
            parse_mode=ParseMode.MARKDOWN
        )

def start(update, context):
    update.message.reply_text("Proxy Scraper Bot is running!")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Start command handler
    dispatcher.add_handler(CommandHandler("start", start))

    # Schedule the proxy scraper job
    job_queue = updater.job_queue
    job_queue.run_repeating(distribute_proxies, interval=3600, first=0)  # Runs every hour

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
