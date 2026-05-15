import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

# =========================
# CONFIG
# =========================

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# =========================

intents = discord.Intents.default()
client = discord.Client(intents=intents)

already_sent = []

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

@client.event
async def on_ready():

    print(f"✅ Logged in as {client.user}")

    channel = client.get_channel(CHANNEL_ID)

    await channel.send("✅ Economic Calendar Bot ONLINE")

    check_news.start()

@tasks.loop(minutes=1)
async def check_news():

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
                forecast_text = forecast.text.strip()
                previous_text = previous.text.strip()

                if actual_text == "":
                    continue

                event_id = f"{currency}-{title}-{actual_text}"

                if event_id in already_sent:
                    continue

                # =========================
                # COLORS + SENTIMENT
                # =========================

                color = 0xffaa00

                gold_sentiment = "➖ Neutral XAUUSD"
                usd_sentiment = "➖ Neutral USD"
                btc_sentiment = "➖ Neutral BTC"

                try:

                    a = float(
                        actual_text
                        .replace("%", "")
                        .replace("K", "")
                        .replace("M", "")
                    )

                    f = float(
                        forecast_text
                        .replace("%", "")
                        .replace("K", "")
                        .replace("M", "")
                    )

                    # =========================
                    # USD
                    # =========================

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

                # =========================
                # EMBED
                # =========================

                embed = discord.Embed(
                    title="🚨 HIGH IMPACT ECONOMIC NEWS",
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

            except Exception as e:
                print(e)

    except Exception as e:
        print(e)

client.run(TOKEN)