import asyncio
import os

from dotenv import load_dotenv

from momo_tracker.bot import MomoTracker


async def main() -> None:
    load_dotenv()
    channel_secret = os.getenv("LINE_CHANNEL_SECRET")
    access_token = os.getenv("LINE_ACCESS_TOKEN")
    if not (channel_secret and access_token):
        raise RuntimeError("LINE_CHANNEL_SECRET and LINE_ACCESS_TOKEN are required.")

    bot = MomoTracker(
        channel_secret,
        access_token,
        os.getenv("DB_URL") or "sqlite://db.sqlite3",
    )
    await bot.run(port=7040, custom_route="/momo/line")


asyncio.run(main())
