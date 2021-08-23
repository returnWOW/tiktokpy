import asyncio
import time
from typing import List

import pyppeteer
from tqdm import tqdm

from tiktokpy.client import Client
from tiktokpy.utils.client import catch_response_and_store
from tiktokpy.utils.logger import logger


class Trending:
    def __init__(self, client: Client):
        self.client: Client = client

    async def feed(self, amount: int, lang: str = "en", page=None):
        if not page:
            page = await self.client.new_page(blocked_resources=["media", "image", "font"])

        self.client.delete_cache_files()
        # await page.setCacheEnabled(False)

        logger.debug('📨 Request "Trending" page')

        result: List[dict] = []
        # list_queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        page.on(
            "response",
            lambda res: asyncio.create_task(catch_response_and_store(res, result))
        )

        time.sleep(3)

        _ = await self.client.goto(
            "/foryou",
            query_params={"lang": lang},
            page=page,
        )
        time.sleep(2)
        logger.debug('📭 Got response from "Trending" page')

        pbar = tqdm(total=amount, desc=f"📈 Getting trending {lang.upper()}")
        pbar.n = min(len(result), amount)
        pbar.refresh()

        while len(result) < amount:
            print("循环获取数据")
            # time.sleep(1000)

            logger.debug("🖱 Trying to scroll to last video item")

            last_child_selector = 'div[class*="-ItemContainer"]:last-child'
            scroll_command = """
                document.querySelector('{selector}')
                    .scrollIntoView();
                """
            try:
                await page.evaluate(scroll_command.format(selector=last_child_selector))
            except pyppeteer.errors.ElementHandleError:
                last_child_selector = ".video-feed-container > .lazyload-wrapper:last-child"
                await page.evaluate(scroll_command.format(selector=last_child_selector))

            await page.waitFor(1_000)

            elements = await page.JJ(".video-feed-item")
            logger.debug(f"🔎 Found {len(elements)} items for clear")

            pbar.n = min(len(result), amount)
            pbar.refresh()

            if len(elements) < 500:
                logger.debug("🔻 Too less for clearing page")
                continue

            await page.JJeval(
                ".video-feed-container > .lazyload-wrapper:not(:last-child)",
                pageFunction="(elements) => elements.forEach(el => el.remove())",
            )
            logger.debug(f"🎉 Cleaned {len(elements) - 1} items from page")
            await page.waitFor(30_000)

        await page.close()
        pbar.close()
        return result[:amount]
