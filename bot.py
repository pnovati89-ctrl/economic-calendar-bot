import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

already_sent = []
daily_events = []

# ==========================================
# READY
# ==========================================

@client.event
async def on_ready():

    print(f"✅ Logged in as {client.user}")

    morning_news.start()
    live_news.start()

# ==========================================
# MORNING NEWS
# ==========================================

@tasks.loop(minutes=60)
async def morning_news():

    now = datetime.utcnow()

    # 08:00 ITA circa
    if now.hour != 6:
        return

    try:

        url = "https://www.forexfactory.com/calendar"

        response = requests.get(url, headers=HEADERS)

        soup = BeautifulSoup(response.text, "lxml")

        rows = soup.find_all("tr", class_="calendar__row")

        channel = client.get_channel(CHANNEL_ID)

        for row in rows:

            try:

                currency = row.get("data-event-currency", "")
                impact = row.get("data-impact", "")
                title = row.get("data-event-title", "")

                if impact.lower() != "high":
                    continue

                forecast = row.find("td", class_="calendar__forecast")
                previous = row.find("td", class_="calendar__previous")
                time_data = row.find("td", class_="calendar__time")

                forecast_text = forecast.text.strip() if forecast else "N/A"
                previous_text = previous.text.strip() if previous else "N/A"
                time_text = time_data.text.strip() if time_data else "TBD"

                event_id = f"{currency}-{title}-{forecast_text}"

                if event_id in daily_events:
                    continue

                embed = discord.Embed(
                    title="📅 TODAY HIGH IMPACT NEWS",
                    description=f"💱 **{currency} - {title}**",
                    color=0xffaa00,
                    timestamp=datetime.utcnow()
                )

                embed.add_field(
                    name="🕒 Release Time",
                    value=f"```{time_text}```",
                    inline=False
                )

                embed.add_field(
                    name="🔵 Forecast",
                    value=f"```{forecast_text}```",
                    inline=True
                )

                embed.add_field(
                    name="⚪ Previous",
                    value=f"```{previous_text}```",
                    inline=True
                )

                embed.add_field(
                    name="🟡 Actual",
                    value="```Waiting...```",
                    inline=True
                )

                embed.add_field(
                    name="🥇 GOLD",
                    value="➖ Neutral",
                    inline=False
                )

                embed.add_field(
                    name="💵 USD",
                    value="➖ Neutral",
                    inline=False
                )

                embed.add_field(
                    name="₿ BTC",
                    value="➖ Neutral",
                    inline=False
                )

                embed.add_field(
                    name="🔥 Impact",
                    value="HIGH",
                    inline=False
                )

                embed.set_footer(
                    text="Powered by ForexFactory"
                )

                await channel.send(embed=embed)

                daily_events.append(event_id)

            except:
                pass

    except Exception as e:
        print(e)

# ==========================================
# LIVE NEWS
# ==========================================

@tasks.loop(minutes=1)
async def live_news():

    try:

        url = "https://www.forexfactory.com/calendar"

        response = requests.get(url, headers=HEADERS)

        soup = BeautifulSoup(response.text, "lxml")

        rows = soup.find_all("tr", class_="calendar__row")

        channel = client.get_channel(CHANNEL_ID)

        for row in rows:

            try:

                currency = row.get("data-event-currency", "")
                impact = row.get("data-impact", "")
                title = row.get("data-event-title", "")

                if impact.lower() != "high":
                    continue

                actual = row.find("td", class_="calendar__actual")
                forecast = row.find("td", class_="calendar__forecast")
                previous = row.find("td", class_="calendar__previous")

                if not actual:
                    continue

                actual_text = actual.text.strip()

                if actual_text == "":
                    continue

                forecast_text = forecast.text.strip() if forecast else "N/A"
                previous_text = previous.text.strip() if previous else "N/A"

                event_id = f"{currency}-{title}-{actual_text}"

                if event_id in already_sent:
                    continue

                color = 0xffaa00

                gold_sentiment = "➖ Neutral"
                usd_sentiment = "➖ Neutral"
                btc_sentiment = "➖ Neutral"

                try:

                    a = float(actual_text.replace("%", "").replace("K", "").replace("M", ""))
                    f = float(forecast_text.replace("%", "").replace("K", "").replace("M", ""))

                    if a > f:

                        color = 0x00ff88

                        usd_sentiment = "📈 Bullish USD"
                        gold_sentiment = "📉 Bearish XAUUSD"
                        btc_sentiment = "📉 Bearish BTC"

                    elif a < f:

                        color = 0xff4444

                        usd_sentiment = "📉 Bearish USD"
                        gold_sentiment = "📈 Bullish XAUUSD"
                        btc_sentiment = "📈 Bullish BTC"

                except:
                    pass

                embed = discord.Embed(
                    title="🚨 DATA RELEASED",
                    description=f"💱 **{currency} - {title}**",
                    color=color,
                    timestamp=datetime.utcnow()
                )

                embed.add_field(
                    name="🟢 Actual",
                    value=f"```{actual_text}```",
                    inline=True
                )

                embed.add_field(
                    name="🔵 Forecast",
                    value=f"```{forecast_text}```",
                    inline=True
                )

                embed.add_field(
                    name="⚪ Previous",
                    value=f"```{previous_text}```",
                    inline=True
                )

                embed.add_field(
                    name="🥇 GOLD",
                    value=gold_sentiment,
                    inline=False
                )

                embed.add_field(
                    name="💵 USD",
                    value=usd_sentiment,
                    inline=False
                )

                embed.add_field(
                    name="₿ BTC",
                    value=btc_sentiment,
                    inline=False
                )

                embed.add_field(
                    name="🔥 Impact",
                    value="HIGH",
                    inline=False
                )

                embed.set_footer(
                    text="Powered by ForexFactory"
                )

                await channel.send(embed=embed)

                already_sent.append(event_id)

            except:
                pass

    except Exception as e:
        print(e)

client.run(TOKEN)
