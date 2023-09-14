from typing import Any
from uuid import uuid4

import aiohttp
from line import Bot, Cog, Context, command
from line.models import (
    ButtonsTemplate,
    ConfirmTemplate,
    ImageMessage,
    PostbackAction,
    TemplateMessage,
    URIAction,
)

from ..db_models import User
from ..utils import line_notify

LINE_NOTIFY_OAUTH_URI = "https://notify-bot.line.me/oauth/authorize?openExternalBrowser=1&response_type=code&client_id=RdvWjFh1XtViZ0VbQdqtgc&redirect_uri={redirect_uri}&scope=notify&state={state}&response_mode=form_post"


class SetNotifyCog(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.bot = bot
        self.session: aiohttp.ClientSession = bot.session  # type: ignore

    @command
    async def set_line_notify(self, ctx: Context, reset: bool = False) -> Any:
        user, _ = await User.get_or_create(id=ctx.user_id)
        if reset:
            await self.session.post(
                "https://notify-api.line.me/api/revoke",
                headers={"Authorization": f"Bearer {user.line_notify_token}"},
            )

            user.line_notify_token = None
            user.line_notify_state = None
            await user.save()

        if not user.line_notify_token:
            state = str(uuid4())
            user.line_notify_state = state
            await user.save()

            template = ButtonsTemplate(
                "如欲在追蹤的商品特價時收到通知, 請先設定 LINE Notify",
                [
                    URIAction(
                        label="前往設定",
                        uri=LINE_NOTIFY_OAUTH_URI.format(
                            state=state,
                            redirect_uri="https://linebot.seriaati.xyz/momo/line-notify",
                        ),
                    )
                ],
                title="通知設定",
            )
            image = ImageMessage(
                original_content_url="https://i.imgur.com/wPYl7Jx.png",
                preview_image_url="https://i.imgur.com/wPYl7Jx.png",
            )
            await ctx.reply_multiple(
                [
                    TemplateMessage("通知設定", template=template),
                    image,
                ]
            )
        else:
            template = ButtonsTemplate(
                "✅ 設定完成\n\n如欲在追蹤的商品特價時收到通知, 請先設定 LINE Notify",
                [
                    PostbackAction("發送測試訊息", data="cmd=send_test_message"),
                    PostbackAction("重新設定", data="cmd=reset_line_notify"),
                ],
                title="通知設定",
            )
            await ctx.reply_template("通知設定", template=template)

    @command
    async def send_test_message(self, ctx: Context) -> Any:
        user = await User.get(id=ctx.user_id)
        assert user.line_notify_token
        await line_notify(user.line_notify_token, "這是一則測試訊息", self.session)
        template = ButtonsTemplate(
            "已發送測試訊息",
            [
                URIAction(
                    label="點我前往查看", uri="https://line.me/R/oaMessage/%40linenotify"
                )
            ],
        )
        await ctx.reply_template("已發送測試訊息", template=template)

    @command
    async def reset_line_notify(self, ctx: Context) -> Any:
        template = ConfirmTemplate(
            "確定要重新設定 LINE Notify 嗎?",
            [
                PostbackAction("確定", data="cmd=set_line_notify&reset=True"),
                PostbackAction("取消", data="cmd=cancel_set_line_notify"),
            ],
        )
        await ctx.reply_template("確認設定", template=template)

    @command
    async def cancel_set_line_notify(self, ctx: Context) -> Any:
        await ctx.reply_text("已取消")
