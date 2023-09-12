from typing import Any, List

from line import Cog, Context, command
from line.models import (
    ButtonsTemplate,
    PostbackAction,
    QuickReply,
    QuickReplyItem,
    URIAction,
)
from playwright.async_api import Browser
from tortoise.exceptions import IntegrityError

from ..bot_model import MomoTrackerBot
from ..crawler import fetch_item_object
from ..db_models import User
from ..utils import split_list


async def add_item_to_db(*, user_id: str, item_url: str, browser: Browser) -> str:
    user = await User.get(id=user_id)

    item = await fetch_item_object(browser, item_url)
    try:
        await item.save()
    except IntegrityError:
        pass
    else:
        await user.items.add(item)
    return item.name


class ItemCog(Cog):
    def __init__(self, bot: MomoTrackerBot):
        super().__init__(bot)
        self.bot = bot

    @command
    async def view_items(self, ctx: Context, index: int = 0) -> Any:
        user, _ = await User.get_or_create(id=ctx.user_id)

        all_items = await user.items.all()
        split_items = split_list(all_items, 11)
        items = split_items[index]

        quick_reply_items: List[QuickReplyItem] = []
        for item in items:
            quick_reply_item = QuickReplyItem(
                PostbackAction(
                    f"{item.name[:17]}..." if len(item.name) > 20 else item.name,
                    data=f"cmd=view_item&item_id={item.id}",
                )
            )
            quick_reply_items.append(quick_reply_item)
        if index > 0:
            quick_reply_items.insert(
                0,
                QuickReplyItem(
                    action=PostbackAction(
                        label="上一頁", data=f"cmd=view_items&index={index-1}"
                    )
                ),
            )
        if index < len(split_items) - 1:
            quick_reply_items.append(
                QuickReplyItem(
                    action=PostbackAction(
                        label="下一頁", data=f"cmd=view_items&index={index+1}"
                    )
                )
            )
        quick_reply = QuickReply(items=quick_reply_items)

        template = ButtonsTemplate(
            f"目前追蹤了 {len(all_items)} 個商品\n點按下方的按鈕來查看已追蹤商品的詳情",
            [
                PostbackAction(
                    label="追蹤新的商品",
                    data="ignore",
                    fill_in_text="cmd=add_item&item_url=",
                    input_option="openKeyboard",
                    display_text="請直接貼上 momo 商品網址\n輸入後需等待 3~5 秒至程式成功獲取商品\n\n請勿更動前面的英文指令",
                )
            ],
            title="追蹤清單",
        )
        await ctx.reply_template("追蹤清單", template=template, quick_reply=quick_reply)

    @command
    async def view_item(self, ctx: Context, item_id: str) -> Any:
        user = await User.get(id=ctx.user_id)
        item = await user.items.filter(id=item_id).first()
        assert item

        template = ButtonsTemplate(
            item.name,
            [
                PostbackAction(
                    label="取消追蹤",
                    data=f"cmd=remove_item&item_id={item.id}",
                ),
                URIAction(
                    label="前往商品頁面",
                    uri=f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={item.id}&openExternalBrowser=1",
                ),
            ],
        )
        await ctx.reply_template(item.name, template=template)

    @command
    async def add_item(self, ctx: Context, item_url: str) -> Any:
        item_name = await add_item_to_db(
            user_id=ctx.user_id, item_url=item_url, browser=self.bot.browser
        )
        await ctx.reply_text(f"已將 {item_name} 加入追蹤清單")

    @command
    async def remove_item(self, ctx: Context, item_id: str) -> Any:
        user = await User.get(id=ctx.user_id)
        item = await user.items.filter(id=item_id).first()
        assert item
        await user.items.remove(item)
        await ctx.reply_text(f"已取消追蹤 {item.name}")