from typing import Any

import aiohttp
from line import Bot, Cog, Context, command
from line.models import ButtonsTemplate, PostbackAction

from ..tasks import crawl_next_promotion_items, notify_promotion_items

ADMIN_ID = "Udfc687303c03a91398d74cbfd33dcea4"


class AdminCog(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.bot = bot
        self.session: aiohttp.ClientSession = bot.session  # type: ignore

    @command
    async def admin(self, ctx: Context) -> Any:
        if ctx.user_id != ADMIN_ID:
            return await ctx.reply_text("你不是管理員")

        template = ButtonsTemplate(
            "管理員界面",
            [
                PostbackAction("crawl promos", data="cmd=crawl_promos"),
                PostbackAction("notify promos", data="cmd=notify_promotion_items"),
            ],
        )
        await ctx.reply_template("管理員界面", template=template)

    @command
    async def crawl_promos(self, ctx: Context) -> Any:
        if ctx.user_id != ADMIN_ID:
            return await ctx.reply_text("你不是管理員")

        await ctx.reply_text("開始爬取特價商品")
        await crawl_next_promotion_items()

    @command
    async def notify_promotion_items(self, ctx: Context) -> Any:
        if ctx.user_id != ADMIN_ID:
            return await ctx.reply_text("你不是管理員")

        await ctx.reply_text("開始通知特價商品")
        await notify_promotion_items(self.session)
