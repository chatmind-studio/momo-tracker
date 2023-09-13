from typing import Optional

from line import Bot, Cog, Context, command
from line.models import ButtonsTemplate, PostbackAction

from ..db_models import User
from ..utils import line_notify


class SetNotifyCog(Cog):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.bot = bot

    @command
    async def set_line_notify(self, ctx: Context, token: Optional[str] = None):
        user, _ = await User.get_or_create(id=ctx.user_id)
        if not token:
            if not user.line_notify_token:
                display_text = "請直接貼上 LINE Notify 權杖\n\n請勿更動前面的英文指令"
            else:
                display_text = "你已經設定過 LINE Notify 權杖\n輸入新的權杖以更新"
            template = ButtonsTemplate(
                "如欲在追蹤的商品特價時收到通知, 請先設定 LINE Notify\n操作方式可查看「使用說明」",
                [
                    PostbackAction(
                        f"{'輸入' if not user.line_notify_token else '更新'} LINE Notify 權杖",
                        data="ignore",
                        fill_in_text="cmd=set_line_notify&token=",
                        display_text=display_text,
                        input_option="openKeyboard",
                    )
                ],
            )
            return await ctx.reply_template("設定 LINE Notify", template=template)

        success = await line_notify(token, "測試訊息")
        if not success:
            return await ctx.reply_text("無效的 LINE Notify 權杖")

        user.line_notify_token = token
        await user.save()
        await ctx.reply_text("LINE Notify 權杖設置成功")
