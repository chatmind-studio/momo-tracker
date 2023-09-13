from line.models import MessageAction, URIAction
from linebot.v3.messaging import (
    RichMenuArea,
    RichMenuBounds,
    RichMenuRequest,
    RichMenuSize,
)

RICH_MENU = RichMenuRequest(
    size=RichMenuSize(width=1200, height=810),
    selected=True,
    name="rich_menu",
    chatBarText="點擊開啟/關閉選單",
    areas=[
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=0, width=600, height=405),
            action=MessageAction(text="cmd=view_items", label="追蹤商品"),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=600, y=0, width=600, height=405),
            action=URIAction(
                uri="https://www.momoshop.com.tw/main/Main.jsp?openExternalBrowser=1",
                label="momo 官網",
            ),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=0, y=405, width=600, height=405),
            action=MessageAction(text="cmd=set_line_notify", label="通知設定"),
        ),
        RichMenuArea(
            bounds=RichMenuBounds(x=600, y=405, width=600, height=405),
            action=URIAction(
                uri="https://seraiati.notion.site/momo-05cda362419b4c8480ec9b87cdf552ea?pvs=4&openExternalBrowser=1",
                label="使用說明",
            ),
        ),
    ],
)
