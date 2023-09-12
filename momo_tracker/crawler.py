from typing import List

from playwright.async_api import async_playwright

from .db_models import Item, PromotionItem


async def crawl_promos():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        promotion_items: List[PromotionItem] = []
        page = await browser.new_page()
        await page.goto(
            "https://www.momoshop.com.tw/edm/cmmedm.jsp?lpn=O1K5FBOqsvN&n=1"
        )

        items = await page.query_selector_all(
            "body > div#BodyBase:nth-child(3) > div > div.bt_2_layout_new > div.container_top:nth-child(13) > div.mainArea:nth-child(3) > div#CustExclbuy.container:nth-child(4) > div.MENTAL:nth-child(4) > ul.product_Area:nth-child(3) > li.box1"
        )

        for item in items:
            price_div = await item.query_selector("div.price > span#nPrice_1")
            url_div = await item.query_selector("div.topnavArea > a#gdsHref_1")
            image_div = await item.query_selector("div.productImage > img")
            brand_name_div = await item.query_selector("div.brand")
            name_div = await item.query_selector("div.brand2")
            price_div = await item.query_selector("div.price > span#nPrice_1")
            remain_count_div = await item.query_selector("div.last > span#gdsStock_1")
            discount_rate_div = await item.query_selector(
                "div.discountArea > div.discount > span#discAmt_1"
            )
            original_price_div = await item.query_selector(
                "div.discountArea > div.oldPrice > span#sPrice_1"
            )

            if not (
                price_div
                and url_div
                and image_div
                and brand_name_div
                and name_div
                and price_div
                and remain_count_div
                and discount_rate_div
                and original_price_div
            ):
                continue

            price = await price_div.inner_text()
            url = await url_div.get_attribute("href")
            if not url:
                continue

            brand_name = await brand_name_div.inner_text()
            name = await name_div.inner_text()
            remain_count = await remain_count_div.inner_text()
            original_price = await original_price_div.inner_text()
            discount_rate = await discount_rate_div.inner_text()

            promotion_items.append(
                PromotionItem(
                    id=url.split("i_code=")[1].split("&")[0],
                    url=f"https:{url}",
                    original_price=int(original_price.replace("$", "")),
                    discount_price=int(price.replace(",", "")),
                    discount_rate=int(discount_rate),
                    name=name,
                    brand_name=brand_name,
                    remain_count=int(remain_count),
                )
            )
        await page.close()
        await browser.close()

        return promotion_items


async def fetch_item_object(item_url: str) -> Item:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(item_url)

        name_div = await page.query_selector("span#osmGoodsName")
        if not name_div:
            name = ""
        else:
            name = await name_div.inner_text()

        item_id = page.url.split("i_code=")[1].split("&")[0]
        await page.close()
        await browser.close()

        return Item(id=item_id, name=name)
