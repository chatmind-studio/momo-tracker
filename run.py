import asyncio
import os
import sys

import aiohttp
from dotenv import load_dotenv

from momo_tracker.bot import MomoTracker


async def main() -> None:
    load_dotenv()
    channel_secret = os.getenv("LINE_CHANNEL_SECRET")
    access_token = os.getenv("LINE_ACCESS_TOKEN")
    if not (channel_secret and access_token):
        raise RuntimeError("LINE_CHANNEL_SECRET and LINE_ACCESS_TOKEN are required.")

    connector = aiohttp.TCPConnector(limit=500)
    async with aiohttp.ClientSession(connector=connector) as session:
        bot = MomoTracker(
            channel_secret,
            access_token,
            os.getenv("DB_URL") or "sqlite://db.sqlite3",
            session,
        )
        await bot.run(port=7040, custom_route="/momo/line")


if sys.platform == "linux":
    import uvloop

    if sys.version_info >= (3, 11):
        with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
            runner.run(main())
    else:
        uvloop.install()
        asyncio.run(main())
else:
    asyncio.run(main())
