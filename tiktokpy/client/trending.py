import asyncio
import time
from typing import List

import pyppeteer
from tqdm import tqdm

from tiktokpy.client import Client
from tiktokpy.utils.client import catch_response_and_store, get_dt_str, get_media_desc_tags, check_num_and_alpha
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

    async def search(self, amount: int, lang: str = "en", page=None, kw="nike", dbSession=None, dbobj=None, kwdbobj=None):
        if not page:
            page = await self.client.new_page(blocked_resources=["media", "image", "font"])

        self.client.delete_cache_files()
        # await page.setCacheEnabled(False)

        logger.debug('📨 Request "Trending" page')

        result: List[dict] = []
        # list_queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        page.on(
            "response",
            lambda res: asyncio.create_task(catch_response_and_store(res, result, "/api/search/general/full", "data"))
        )

        time.sleep(3)

        # https://www.tiktok.com/search?q=nike&t=1632749856755
        _ = await self.client.goto(
            "/search",
            query_params={"q": kw, "t": int(time.time() * 1000)},
            page=page,
        )
        time.sleep(10)
        logger.debug('📭 Got response from search page')

        pbar = tqdm(total=amount, desc=f"📈 Getting trending {lang.upper()}")
        pbar.n = min(len(result), amount)
        pbar.refresh()

        save_idx = 0
        old_save_idx = 0

        def save_data():
            nonlocal save_idx
            
            if len(result) > save_idx and dbSession:
                lRet = len(result)
                idx = 0
                for i in range(save_idx, lRet):
                    # print(result[i])
                    idx += 1
                    if "user_list" in result[i]:
                        continue

                    ret = dbSession.query(dbobj).filter(dbobj.shipinid==result[i]["item"]["id"]).first()
                    if ret:
                        logger.warning("video is saved")
                        continue
                    
                    data = result[i]["item"]
                    obj = dbobj(fabuzhe=data["author"]["uniqueId"], shipinid=data["id"], shifoucaijipinglunzhe=False, shifoucaijidianzanzhe=False, shijian=get_dt_str())
                    dbSession.add(obj)
                    dbSession.commit()
                    logger.debug("Add to db: {}".format(data))
                    tags = get_media_desc_tags(data["desc"], logger)
                    for tag in tags:
                        if check_num_and_alpha(tag):
                            if dbSession.query(kwdbobj).filter(kwdbobj.tagci==tag).first():
                                logger.warning("has tag, skip")
                                continue

                            kwobj = kwdbobj(tagci=tag, shifouqiyong=False, shifouzhixingwanbi=False)
                            dbSession.add(kwobj)
                            dbSession.commit()
                            logger.debug("add tag: {}".format(tag))

                save_idx += idx

        loop_idx = 0
        while save_idx < amount:
            logger.debug("loop to get data")
            loop_idx += 1

            if loop_idx >= 20 and (save_idx == old_save_idx or save_idx == 0):
                logger.warning("Can't get data any more, break loop")
                break
            # time.sleep(1000)

            logger.debug("🖱 Trying to scroll to last video item")

            last_child_selector = 'button[class*="ButtonMore"]'
            scroll_command = """
                document.querySelector('{selector}')
                    .scrollIntoView();
                """
            idx = 0
            while idx <= 20:
                try:
                    await page.evaluate(scroll_command.format(selector=last_child_selector))
                    break
                except pyppeteer.errors.ElementHandleError:
                    idx += 1
                    time.sleep(1)
                    print("click error: sleep and retry：{}".format(idx))
                    continue
                # last_child_selector = ".video-feed-container > .lazyload-wrapper:last-child"
                # await page.evaluate(scroll_command.format(selector=last_child_selector))

            await page.waitFor(1_000)

            # elements = await page.JJ(".video-feed-item")
            # logger.debug(f"🔎 Found {len(elements)} items for clear")

            pbar.n = min(save_idx, amount)
            pbar.refresh()
            save_data()

            # if len(elements) < 500:
            #     logger.debug("🔻 Too less for clearing page")
            #     continue

            await page.waitFor(30_000)
            elem = await page.JJ('button[class*="ButtonMore"]')
            await elem[0].click()
            # time.sleep(5)

        # save_data()

        await page.close()
        pbar.close()
        return result[:amount]