import logging
import os
from pathlib import Path
from typing import Any

import aiohttp
from aiohttp import web
from dotenv import load_dotenv
from line import Bot, Context
from tortoise import Tortoise

from .cogs.item import add_item_to_db
from .crawler import crawl_promos
from .db_models import User
from .rich_menu import RICH_MENU
from .tasks import notify_promotion_items
from .utils import extract_url, get_now, line_notify

load_dotenv()

LINE_NOTIFY_SECRET = os.getenv("LINE_NOTIFY_SECRET")
if not LINE_NOTIFY_SECRET:
    raise RuntimeError("LINE_NOTIFY_SECRET is required.")


class MomoTracker(Bot):
    def __init__(
        self,
        channel_secret: str,
        access_token: str,
        db_url: str,
        session: aiohttp.ClientSession,
    ) -> None:
        super().__init__(channel_secret=channel_secret, access_token=access_token)
        self.db_url = db_url
        self.session = session

    async def _setup_rich_menu(self) -> None:
        result = await self.line_bot_api.create_rich_menu(RICH_MENU)
        with open("data/rich_menu.png", "rb") as f:
            await self.blob_api.set_rich_menu_image(
                result.rich_menu_id,
                body=bytearray(f.read()),
                _headers={"Content-Type": "image/png"},
            )
        await self.line_bot_api.set_default_rich_menu(result.rich_menu_id)

    async def line_notify_callback(self, request: web.Request) -> web.Response:
        params = await request.post()
        code = params.get("code")
        state = params.get("state")
        redirect_url = "https://line.me/R/oaMessage/%40181ucqqr"

        user = await User.get_or_none(line_notify_state=state)
        if user:
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": "https://linebot.seriaati.xyz/momo/line-notify",
                "client_id": "RdvWjFh1XtViZ0VbQdqtgc",
                "client_secret": LINE_NOTIFY_SECRET,
            }
            async with self.session.post(
                "https://notify-bot.line.me/oauth/token", data=data
            ) as resp:
                resp_data = await resp.json()
                user.line_notify_token = resp_data["access_token"]
                user.line_notify_state = None
                await user.save()

        return web.Response(
            status=302,
            headers={"Location": redirect_url},
        )

    async def setup_hook(self) -> None:
        for cog in Path("momo_tracker/cogs").glob("*.py"):
            if cog.stem == "__init__":
                continue
            logging.info("Loading cog %s", cog.stem)
            self.add_cog(f"momo_tracker.cogs.{cog.stem}")

        logging.info("Setting up rich menu")
        await self._setup_rich_menu()

        logging.info("Setting up database")
        await Tortoise.init(
            db_url=self.db_url,
            modules={"models": ["momo_tracker.db_models"]},
        )
        await Tortoise.generate_schemas()

        logging.info("Setting up webhook")
        self.app.add_routes([web.post("/momo/line-notify", self.line_notify_callback)])

    async def handle_no_cmd(self, ctx: Context, text: str) -> Any:
        url = extract_url(text)
        if url and ("momoshop.com" in url or "momo.dm" in url):
            await ctx.reply_text(
                "機器人正在處理這項商品 (需約 5~7 秒), 如果你有進行「通知設定」, 將會在商品成功加入追蹤清單時收到通知"
            )

            user, _ = await User.get_or_create(id=ctx.user_id)
            try:
                item_name = await add_item_to_db(
                    user=user, item_url=url, session=self.session
                )
            except IndexError:
                if user.line_notify_token:
                    await line_notify(
                        user.line_notify_token, f"這個商品連結 ({url}) 是無效的", self.session
                    )
            else:
                if user.line_notify_token:
                    await line_notify(
                        user.line_notify_token,
                        f"已加入追蹤清單: {item_name} ({url})",
                        self.session,
                    )
        else:
            await ctx.reply_text("這個商品連結是無效的")

    async def run_tasks(self) -> None:
        now = get_now()
        if now.hour in (23, 7, 11, 15, 20) and now.minute < 1:
            logging.info("Crawling promotion items")
            await crawl_promos()
        elif now.hour in (0, 8, 12, 16, 21) and now.minute < 1:
            logging.info("Notifying promotion items")
            await notify_promotion_items(self.session)

    async def on_close(self) -> None:
        await Tortoise.close_connections()
