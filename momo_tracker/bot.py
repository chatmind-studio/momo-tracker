import logging
from pathlib import Path
from typing import Any

from line import Bot, Context
from playwright.async_api import Browser, Playwright
from tortoise import Tortoise

from .cogs.item import add_item_to_db
from .crawler import crawl_promos
from .db_models import Item, PromotionItem
from .rich_menu import RICH_MENU
from .utils import extract_url, get_now, line_notify


class MomoTracker(Bot):
    def __init__(
        self,
        channel_secret: str,
        access_token: str,
        db_url: str,
        playwright: Playwright,
    ) -> None:
        super().__init__(channel_secret=channel_secret, access_token=access_token)
        self.db_url = db_url
        self.playwright = playwright
        self.browser: Browser

    async def _setup_rich_menu(self) -> None:
        result = await self.line_bot_api.create_rich_menu(RICH_MENU)
        with open("data/rich_menu.png", "rb") as f:
            await self.blob_api.set_rich_menu_image(
                result.rich_menu_id,
                body=bytearray(f.read()),
                _headers={"Content-Type": "image/png"},
            )
        await self.line_bot_api.set_default_rich_menu(result.rich_menu_id)

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

        logging.info("Opening browser")
        self.browser = await self.playwright.chromium.launch()

    async def handle_no_cmd(self, ctx: Context, text: str) -> Any:
        url = extract_url(text)
        if url and ("momoshop.com" in url or "momo.dm" in url):
            item_name = await add_item_to_db(
                user_id=ctx.user_id, item_url=url, browser=self.browser
            )
            await ctx.reply_text(f"已將 {item_name} 加入追蹤清單")

    async def run_tasks(self) -> None:
        now = get_now()
        if now.hour in (0, 8, 12, 16, 21) and now.minute < 1:
            promotion_items = await PromotionItem.all()
            items = await Item.all()
            for promotion_item in promotion_items:
                for item in items:
                    if item.id == promotion_item.id:
                        users = await item.users.all()
                        message = f"{item.name} 正在特價!\n原價: ${promotion_item.original_price}\n特價: ${promotion_item.discount_price}\n下殺 {promotion_item.discount_rate} 折\n剩下 {promotion_item.remain_count} 組\n商品連結: {promotion_item.url}\n搶購頁面: https://www.momoshop.com.tw/edm/cmmedm.jsp?lpn=O1K5FBOqsvN"
                        for user in users:
                            if user.line_notify_token:
                                await line_notify(user.line_notify_token, message)

            await PromotionItem.all().delete()
            next_promotion_items = await crawl_promos(self.browser)
            for item in next_promotion_items:
                await item.save()

    async def on_close(self) -> None:
        await Tortoise.close_connections()
