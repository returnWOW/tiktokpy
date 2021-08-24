import asyncio
from typing import List

import pyppeteer
from pyppeteer.page import Page
from tqdm import tqdm
import pdb

from tiktokpy.client import Client
from tiktokpy.utils.client import catch_response_and_store, catch_response_info
from tiktokpy.utils.logger import logger

import re

pattern_comments = re.compile(r'<div .*? comment-content .*?"><a href="/@(.*?)\?.*?".*?username">(.*?)</span></a><p class=".*? comment-text"><span class=".*?">(.*?)</span>', re.S)

# <div .*? comment-content .*?"><a href="/@(.*?)\?.*?" .*?username">(.*?)</span></a><p class=".*? comment-text"><span class=".*?">(.*?)</span>


class User:
    def __init__(self, client: Client):
        self.client = client

    async def like(self, username: str, video_id: str, page=None):
        self.client.delete_cache_files()
        if not page:
            page: Page = await self.client.new_page(blocked_resources=["image", "media", "font"])

        logger.debug(f"👥 Like video id {video_id} of @{username}")

        like_info_queue: asyncio.Queue = asyncio.Queue(maxsize=1)

        page.on(
            "response",
            lambda res: asyncio.create_task(
                catch_response_info(res, like_info_queue, "/commit/item/digg"),
            ),
        )

        logger.info(f"🧭 Going to @{username}'s video {video_id} page for like")

        await self.client.goto(
            f"/@{username}/video/{video_id}",
            page=page,
            options={"waitUntil": "networkidle0"},
        )

        like_selector = ".lazyload-wrapper:first-child .item-action-bar.vertical > .bar-item-wrapper:first-child"  # noqa: E501
        is_liked = await page.J(f'{like_selector} svg[fill="none"]')

        if is_liked:
            logger.info(f"😏 @{username}'s video {video_id} already liked")
            return

        await page.click(like_selector)

        like_info = await like_info_queue.get()

        if like_info["status_code"] == 0:
            logger.info(f"👍 @{username}'s video {video_id} liked")
        else:
            logger.warning(f"⚠️  @{username}'s video {video_id} probably not liked")

        await page.close()

    async def unlike(self, username: str, video_id: str):
        page: Page = await self.client.new_page(blocked_resources=["image", "media", "font"])
        logger.debug(f"👥 Unlike video id {video_id} of @{username}")

        like_info_queue: asyncio.Queue = asyncio.Queue(maxsize=1)

        page.on(
            "response",
            lambda res: asyncio.create_task(
                catch_response_info(res, like_info_queue, "/commit/item/digg"),
            ),
        )

        logger.info(f"🧭 Going to @{username}'s video {video_id} page for unlike")

        await self.client.goto(
            f"/@{username}/video/{video_id}",
            page=page,
            options={"waitUntil": "networkidle0"},
        )

        like_selector = ".lazyload-wrapper:first-child .item-action-bar.vertical > .bar-item-wrapper:first-child"  # noqa: E501
        is_unliked = await page.J(f'{like_selector} svg[fill="currentColor"]')

        if is_unliked:
            logger.info(f"😏 @{username}'s video {video_id} already unliked")
            return

        await page.click(like_selector)

        like_info = await like_info_queue.get()

        if like_info["status_code"] == 0:
            logger.info(f"👎 @{username}'s video {video_id} unliked")
        else:
            logger.warning(f"⚠️  @{username}'s video {video_id} probably not unliked")

        await page.close()

    async def follow(self, username: str, page=None):
        self.client.delete_cache_files()
        if not page:
            page: Page = await self.client.new_page(blocked_resources=["image", "media", "font"])

        logger.debug(f"👥 Follow {username}")

        # follow_info_queue: asyncio.Queue = asyncio.Queue(maxsize=10)

        # page.on(
        #     "response",
        #     lambda res: asyncio.create_task(
        #         catch_response_info(res, follow_info_queue, "/commit/follow/user"),
        #     ),
        # )

        logger.info(f"🧭 Going to {username}'s page for following")

        await self.client.goto(
            f"/@{username.lstrip('@')}",
            page=page,
            options={"waitUntil": "networkidle0"},
        )

        follow_title: str = await page.Jeval(
            ".follow-button",
            pageFunction="element => element.textContent",
        )

        logger.debug("follow title: |{}|".format(follow_title))
        if follow_title.lower() not in ("follow", "关注", "關註", "關注"):
            logger.info(f"😏 {username} already followed")
            return

        await page.click(".follow-button")

        # follow_info = await follow_info_queue.get()

        # if follow_info["status_code"] == 0:
        #     logger.info(f"➕ {username} followed")
        # else:
        #     logger.warning(f"⚠️  {username} probably not followed")

        await page.close()

    async def unfollow(self, username: str):
        page: Page = await self.client.new_page(blocked_resources=["image", "media", "font"])
        logger.debug(f"👥 Unfollow {username}")

        unfollow_info_queue: asyncio.Queue = asyncio.Queue(maxsize=1)

        page.on(
            "response",
            lambda res: asyncio.create_task(
                catch_response_info(res, unfollow_info_queue, "/commit/follow/user"),
            ),
        )

        logger.info(f"🧭 Going to {username}'s page for unfollowing")

        await self.client.goto(
            f"/@{username.lstrip('@')}",
            page=page,
            options={"waitUntil": "networkidle0"},
        )

        follow_title: str = await page.Jeval(
            ".follow-button",
            pageFunction="element => element.textContent",
        )

        if follow_title.lower() != "following":
            logger.info(f"😏 {username} already unfollowed")
            return

        await page.click(".follow-button")

        unfollow_info = await unfollow_info_queue.get()

        if unfollow_info["status_code"] == 0:
            logger.info(f"➖ {username} unfollowed")
        else:
            logger.warning(f"⚠️  {username} probably not unfollowed")

        await page.close()

    async def feed(self, username: str, amount: int, page=None):
        self.client.delete_cache_files()
        if not page:
            page: Page = await self.client.new_page(blocked_resources=["image", "media", "font"])

        logger.debug(f"📨 Request {username} feed")

        result: List[dict] = []

        page.on(
            "response",
            lambda res: asyncio.create_task(catch_response_and_store(res, result, "/post/item_list/")),
        )

        _ = await self.client.goto(f"/{username}", page=page, options={"waitUntil": "networkidle0"})
        logger.debug(f"📭 Got {username} feed")

        await page.waitForSelector(".video-feed-item", options={"visible": True})

        pbar = tqdm(total=amount, desc=f"📈 Getting {username} feed")
        pbar.n = min(len(result), amount)
        pbar.refresh()

        attempts = 0
        last_result = len(result)

        while len(result) < amount:
            logger.debug("🖱 Trying to scroll to last video item")
            await page.evaluate(
                """
                document.querySelector('.video-feed-item:last-child')
                    .scrollIntoView();
            """,
            )
            
            await page.waitFor(1_000)

            elements = await page.JJ(".video-feed-item")
            logger.debug(f"🔎 Found {len(elements)} items for clear")

            pbar.n = min(len(result), amount)
            pbar.refresh()

            if last_result == len(result):
                attempts += 1
            else:
                attempts = 0

            if attempts > 10:
                pbar.clear()
                pbar.total = len(result)
                logger.info(
                    f"⚠️  After 10 attempts found {len(result)} videos. "
                    f"Probably some videos are private",
                )
                break

            last_result = len(result)

            if len(elements) < 500:
                logger.debug("🔻 Too less for clearing page")
                continue

            await page.JJeval(
                ".video-feed-item:not(:last-child)",
                pageFunction="(elements) => elements.forEach(el => el.remove())",
            )
            logger.debug(f"🎉 Cleaned {len(elements) - 1} items from page")
            await page.waitFor(30_000)

        await page.close()
        pbar.close()
        return result[:amount]

    async def get_comments(self, username: str, media_id: int, amount: int, page=None):
        self.client.delete_cache_files()
        if not page:
            page: Page = await self.client.new_page(blocked_resources=["image", "media", "font"])
        logger.debug(f"📨 Request {username} feed")

        result: List[dict] = []
        ret = {}

        # page.on(
        #     "response", 
        #     lambda res: asyncio.create_task(catch_response_and_store(res, result, "/comment/list/")),
        # )

        _ = await self.client.goto(f"/@{username}/video/{media_id}?lang=en&is_copy_url=1&is_from_webapp=v1", page=page, options={"waitUntil": "networkidle0"})
        logger.debug(f"📭 Got {username} feed")

        elem = await page.JJ('span[class*="event-delegate-mask"]')
        print(elem)
        if not elem:
            print("video comment button not found")
            return 
        await elem[0].click()
        # input("测试")
        await asyncio.sleep(5)

        pbar = tqdm(total=amount, desc=f"📈 Getting {username} {media_id} comments")
        pbar.n = min(len(result), amount)
        pbar.refresh()

        attempts = 0
        last_result = len(result)

        while len(result) < amount:
            logger.debug("🖱 Trying to scroll to last comment item")
            try:
                await page.evaluate(
                    """
                    document.querySelector('.comments > .comment-item:last-child')
                        .scrollIntoView();
                """,
                )
                # last_child_selector = ".video-feed-container > .lazyload-wrapper:last-child"
            except pyppeteer.errors.ElementHandleError as e:
                print(e)
                # return result[:amount]
                pass

            content = await page.content()
            # with open("comments_html.html", "w", encoding="utf-8") as fout:
            #     fout.write(content)

            for e in pattern_comments.findall(content):
                print(e)
                # result.append(e)
                if ret.get(e[0]):
                    if e[2] in ret[e[0]][1]:
                        continue
                    else:
                        result.append(e)
                else:
                    ret[e[0]] = [e[1], set()]
                    ret[e[0]][1].add(e[2])
                    result.append(e)

            await page.waitFor(1_000)
            
            print(result)

            pbar.n = min(len(result), amount)
            pbar.refresh()

            if last_result == len(result):
                attempts += 1
            else:
                attempts = 0

            if attempts > 5:
                pbar.clear()
                pbar.total = len(result)
                logger.info(
                    f"⚠️  After 10 attempts found {len(result)} videos. "
                    f"Probably some videos are private",
                )
                break

            last_result = len(result)

            await page.waitFor(30_000)

        await page.close()
        pbar.close()
        return result[:amount]

    async def comment(self, username: str, media_id: int, content: str, page=None):
        self.client.delete_cache_files()
        if not page:
            page: Page = await self.client.new_page(blocked_resources=["image", "media", "font"])
        logger.debug(f"📨 Request {username} feed")

        _ = await self.client.goto(f"/@{username}/video/{media_id}?lang=en&is_copy_url=1&is_from_webapp=v1", page=page, options={"waitUntil": "networkidle0"})
        logger.debug(f"📭 Got {username} feed")

        elem = await page.JJ('span[class*="event-delegate-mask"]')
        print(elem)
        if not elem:
            print("video comment button not found")
            return 
        await elem[0].click()
        # input("测试")
        await asyncio.sleep(5)

        comment_input = await page.J('div[class*="public-DraftStyleDefault-block"]')
        print(comment_input)
        await comment_input.click()
        await page.keyboard.type(content)
        await asyncio.sleep(3)


        comment_submit = await page.J('div[class*="post-container"]')
        print(comment_submit)
        await comment_submit.click()