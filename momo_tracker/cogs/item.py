from typing import Any, List, Union

import aiohttp
from line import Bot, Cog, Context, command
from line.models import (
    CarouselColumn,
    CarouselTemplate,
    ConfirmTemplate,
    PostbackAction,
    QuickReply,
    QuickReplyItem,
    TemplateMessage,
    TextMessage,
    URIAction,
)
from tortoise.exceptions import IntegrityError

from ..crawler import fetch_item_object
from ..db_models import Item, User
from ..utils import split_list


async def add_item_to_db(
    *, user: User, item_url: str, session: aiohttp.ClientSession
) -> str:
    item = await fetch_item_object(item_url, session)
    try:
        await item.save()
    except IntegrityError:
        item = await Item.get(id=item.id)

    await user.items.add(item)
    return item.name


class ItemCog(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.bot = bot

    @staticmethod
    async def view_items_message(
        ctx: Context, index: int = 0
    ) -> Union[TemplateMessage, TextMessage]:
        user, _ = await User.get_or_create(id=ctx.user_id)
        all_items = await user.items.all()
        if not all_items:
            return TextMessage(
                "你尚未追蹤任何商品, 追蹤商品後才能在特價時收到通知\n追蹤方式: 將 momo 購物網商品頁面的網址分享給機器人\n\n(圖文教學可點擊「使用教學」查看)"
            )

        split_items = split_list(all_items, 10)
        items = split_items[index]
        columns: List[CarouselColumn] = []
        for item in items:
            column = CarouselColumn(
                text=f"{item.name[:57]}..." if len(item.name) > 60 else item.name,
                actions=[
                    PostbackAction(
                        "取消追蹤",
                        data=f"cmd=remove_item&item_id={item.id}",
                    ),
                    URIAction(
                        "前往商品頁面",
                        uri=f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={item.id}&openExternalBrowser=1",
                    ),
                ],
                thumbnail_image_url=item.image_url,
            )
            columns.append(column)

        quick_reply_items: List[QuickReplyItem] = [
            QuickReplyItem(
                action=PostbackAction(label="❌ 取消追蹤所有商品", data="cmd=remove_all_items")
            )
        ]
        if index > 0:
            quick_reply_items.append(
                QuickReplyItem(
                    action=PostbackAction(
                        label="⬅️ 上一頁", data=f"cmd=view_items&index={index-1}"
                    )
                ),
            )
        if index < len(split_items) - 1:
            quick_reply_items.append(
                QuickReplyItem(
                    action=PostbackAction(
                        label="➡️ 下一頁", data=f"cmd=view_items&index={index+1}"
                    )
                )
            )

        return TemplateMessage(
            "追蹤清單",
            template=CarouselTemplate(columns=columns),
            quick_reply=QuickReply(items=quick_reply_items),
        )

    @command
    async def view_items(self, ctx: Context, index: int = 0) -> Any:
        message = await self.view_items_message(ctx, index)
        await ctx.reply_multiple([message])

    @command
    async def remove_item(self, ctx: Context, item_id: str) -> Any:
        user = await User.get(id=ctx.user_id)

        item = await user.items.filter(id=item_id).first()
        assert item
        await user.items.remove(item)

        await ctx.reply_multiple(
            [TextMessage(f"已取消追蹤 {item.name}"), await self.view_items_message(ctx)]
        )

    @command
    async def remove_all_items(self, ctx: Context, confirmed: bool = False) -> Any:
        if not confirmed:
            template = ConfirmTemplate(
                "確定要取消追蹤所有商品嗎?",
                actions=[
                    PostbackAction(
                        label="確定", data="cmd=remove_all_items&confirmed=True"
                    ),
                    PostbackAction(label="取消", data="cmd=cancel"),
                ],
            )
            return await ctx.reply_template("確定嗎?", template=template)

        user = await User.get(id=ctx.user_id)
        await user.items.clear()

        await ctx.reply_multiple(
            [TextMessage("已取消追蹤所有商品"), await self.view_items_message(ctx)]
        )
