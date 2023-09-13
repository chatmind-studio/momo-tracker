from .crawler import crawl_promos
from .db_models import Item, PromotionItem
from .utils import line_notify


async def crawl_next_promotion_items() -> None:
    await PromotionItem.all().delete()
    next_promotion_items = await crawl_promos()
    for item in next_promotion_items:
        await item.save()


async def notify_promotion_items() -> None:
    promo_items = await PromotionItem.all()
    items = await Item.all()
    for promo_item in promo_items:
        for item in items:
            if item.id == promo_item.id:
                original_price = "${:,}".format(promo_item.original_price)
                discount_price = "${:,}".format(promo_item.discount_price)
                discount_rate = (
                    round(promo_item.discount_rate)
                    if promo_item.discount_rate.is_integer()
                    else promo_item.discount_rate
                )

                message = f"{item.name} 正在特價!\n原價: {original_price}\n特價: {discount_price}\n下殺 {discount_rate} 折\n剩下 {promo_item.remain_count} 組\n商品連結: {promo_item.url}\n搶購頁面: https://www.momoshop.com.tw/edm/cmmedm.jsp?lpn=O1K5FBOqsvN"
                users = await item.users.all()
                for user in users:
                    if user.line_notify_token:
                        await line_notify(user.line_notify_token, message)
