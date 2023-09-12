from typing import Any, List

from line import Bot, Cog, Context, command
from line.models import QuickReply, QuickReplyItem, URIAction


class HelpCog(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.bot = bot

    @property
    def help_items(self) -> List[QuickReplyItem]:
        return [
            QuickReplyItem(
                action=URIAction(
                    label="追蹤新的商品",
                    uri="https://seraiati.notion.site/momo-05cda362419b4c8480ec9b87cdf552ea?pvs=4&openExternalBrowser=1",
                )
            ),
            QuickReplyItem(
                action=URIAction(
                    label="設定 LINE Notify",
                    uri="https://seraiati.notion.site/LINE-notify-a3e90b7b0b0a46afafb0c264306b4ce8?pvs=4&openExternalBrowser=1",
                )
            ),
        ]

    @command
    async def help(self, ctx: Context) -> Any:
        await ctx.reply_text(
            "請選擇要查看的使用說明",
            quick_reply=QuickReply(items=self.help_items),
        )
