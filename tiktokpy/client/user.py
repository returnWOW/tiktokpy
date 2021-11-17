import os
import asyncio
from typing import List
import traceback

import pyppeteer
from pyppeteer.page import Page
from tqdm import tqdm
import pdb
import time

from tiktokpy.client import Client
from tiktokpy.utils.client import catch_response_and_store, catch_response_info, get_dt_str, trans_char
from tiktokpy.utils.logger import logger

import re

pattern_comment_area = re.compile(r'comment-container">(.*?)comment-post-outside-container">', re.S)
pattern_comments = re.compile(r'<div .*? comment-content .*?<a href="/@(.*?)\?.*?username">(.*?)</span></a><p .*? comment-text"><span class=".*?">(.*?)</span>', re.S)
# pattern_comments = re.compile(r'<div .*? comment-content .*?<a href="/@(.*?)\?.*?".*?username">(.*?)</span></a><p class=".*? comment-text"><span class=".*?">(.*?)</span>', re.S)

# user post rex
pattern_user_post_id = re.compile(r'data-e2e="user-post-item".*?<a href="http.*?/@.*?/video/(\d+)', re.S)

# <div .*? comment-content .*?"><a href="/@(.*?)\?.*?" .*?username">(.*?)</span></a><p class=".*? comment-text"><span class=".*?">(.*?)</span>


class User:
    def __init__(self, client: Client):
        self.client = client

    async def like(self, username: str, video_id: str, page=None):
        self.client.delete_cache_files()
        if not page:
            page: Page = await self.client.new_page(blocked_resources=["image", "media", "font"])

        page.setDefaultNavigationTimeout(0)
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

        time.sleep(3)

        # like_selector = ".lazyload-wrapper:first-child .item-action-bar.vertical > .bar-item-wrapper:first-child"  # noqa: E501
        # is_liked = await page.J(f'{like_selector} svg[fill="none"]')

        # if is_liked:
        #     logger.info(f"😏 @{username}'s video {video_id} already liked")
        #     return

        click_button = await page.xpath('//span[@data-e2e="like-icon"]/..')
        print(click_button)
        click_button = click_button[0]
        await asyncio.sleep(2)
        await click_button.click()

        # like_info = await like_info_queue.get()

        # if like_info["status_code"] == 0:
        # else:
            # logger.warning(f"⚠️  @{username}'s video {video_id} probably not liked")
        logger.info(f"👍 @{username}'s video {video_id} liked")
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

        page.setDefaultNavigationTimeout(0)
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

        time.sleep(5)

        # follow_title: str = await page.Jeval(
        #     ".follow-button",
        #     pageFunction="element => element.textContent",
        # )
        follow_button = await page.JJ('button[class*="FollowButton"]')
        print(follow_button)
        if not follow_button:
            logger.error("button not found.")
            return 
            
        follow_button = follow_button[0]
        print(dir(follow_button))

        follow_title = await page.evaluate('item => item.textContent', follow_button)
        print(follow_title)

        logger.debug("follow title: |{}|".format(follow_title))
        if follow_title.lower() not in ("follow", "关注", "關註", "關注"):
            logger.info(f"😏 {username} already followed")
            return

        # await page.click(".follow-button")
        await follow_button.click()

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

        time.sleep(5)

        # await page.waitForSelector(".video-feed-item", options={"visible": True})

        pbar = tqdm(total=amount, desc=f"📈 Getting {username} feed")
        pbar.n = min(len(result), amount)
        pbar.refresh()

        attempts = 0
        last_result = len(result)

        while len(result) < amount:
            logger.debug("🖱 Trying to scroll to last video item")
            # await page.evaluate(
            #     """
            #     document.querySelector('.video-feed-item:last-child')
            #         .scrollIntoView();
            # """,
            # )
            
            # await page.waitFor(1_000)

            # elements = await page.JJ(".video-feed-item")
            # logger.debug(f"🔎 Found {len(elements)} items for clear")

            # pbar.n = min(len(result), amount)
            # pbar.refresh()

            # if last_result == len(result):
            #     attempts += 1
            # else:
            #     attempts = 0

            # if attempts > 10:
            #     pbar.clear()
            #     pbar.total = len(result)
            #     logger.info(
            #         f"⚠️  After 10 attempts found {len(result)} videos. "
            #         f"Probably some videos are private",
            #     )
            #     break

            # last_result = len(result)

            # if len(elements) < 500:
            #     logger.debug("🔻 Too less for clearing page")
            #     continue

            # await page.JJeval(
            #     ".video-feed-item:not(:last-child)",
            #     pageFunction="(elements) => elements.forEach(el => el.remove())",
            # )
            # logger.debug(f"🎉 Cleaned {len(elements) - 1} items from page")
            logger.debug("wait for video")
            await page.waitFor(30_000)

        await page.close()
        pbar.close()
        return result[:amount]

    async def feed2(self, username: str, amount: int, page=None):
        if not page:
            page: Page = await self.client.new_page(blocked_resources=["image", "media", "font"])

        logger.debug(f"📨 Request {username} feed")

        result: List[dict] = []

        # page.on(
        #     "response",
        #     lambda res: asyncio.create_task(catch_response_and_store(res, result, "/post/item_list/")),
        # )

        _ = await self.client.goto(f"/{username}", page=page, options={"waitUntil": "networkidle0"})
        logger.debug(f"📭 Got {username} feed")

        time.sleep(5)

        # await page.waitForSelector(".video-feed-item", options={"visible": True})

        pbar = tqdm(total=amount, desc=f"📈 Getting {username} feed")
        pbar.n = min(len(result), amount)
        pbar.refresh()

        attempts = 0
        last_result = len(result)

        idx = 0

        while len(result) < amount:
            logger.debug("🖱 Trying to scroll to last video item")
            idx += 1

            text = await page.content()
            elems = pattern_user_post_id.findall(text)
            if elems:
                for elem in elems:
                    print(elem)
                    result.append(elem)

            print("aproche")
            return result

            logger.debug("wait for video")
            await page.waitFor(30_000)

        await page.close()
        pbar.close()
        return result

    async def get_comments(self, username: str, media_id: int, amount: int, page=None, 
                           dbSession=None, dbobj=None):

        try:
            self.client.delete_cache_files()
            if not page:
                page: Page = await self.client.new_page(blocked_resources=["image", "media", "font"])
            logger.debug(f"📨 Request {username} feed")

            page.setDefaultNavigationTimeout(0)
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

                logger.debug("get page source")
                content = await page.content()
                # with open("comments_html.html", "w", encoding="utf-8") as fout:
                #     fout.write(content)
                comment_area = pattern_comment_area.search(content)
                if not comment_area:
                    logger.error("comment area not found!!!")
                    return []

                logger.debug("parser page source: {}".format(len(content)))
                for e in pattern_comments.findall(comment_area.group(1)):
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

                    if dbSession:
                        text = trans_char(e[2])
                        if dbSession.query(dbobj).filter(dbobj.PingLunZhe==e[0], dbobj.PingLunNeiRong==text, dbobj.FaBuZhe==username).first():
                            logger.debug("saved comment, skip")
                            continue

                        logger.debug("Save commenter: {} de emoji: {}".format(e, text))
                        obj = dbobj(PingLunZhe=e[0], PingLunNeiRong=text, GuanJianCi="", FaBuZhe=username, 
                                    TianJiaShiJian=get_dt_str(), ShiFouGuanZhu=False)
                        dbSession.add(obj)
                        dbSession.commit()

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
        except pyppeteer.errors.TimeoutError as e:
            print(e)
            logger.error(traceback.format_exc())
            input("enter to exit")

    async def comment(self, username: str, media_id: int, content: str, page=None):
        self.client.delete_cache_files()
        if not page:
            page: Page = await self.client.new_page(blocked_resources=["image", "media", "font"])
        logger.debug(f"📨 Request {username} feed")

        page.setDefaultNavigationTimeout(0)

        _ = await self.client.goto(f"/@{username}/video/{media_id}?lang=en&is_copy_url=1&is_from_webapp=v1", page=page, options={"waitUntil": "networkidle0"})
        logger.debug(f"📭 Got {username} feed")

        # elem = await page.JJ('span[class*="event-delegate-mask"]')
        elem = await page.xpath('//span[@data-e2e="comment-icon"]')
        print(elem)
        if not elem:
            print("video comment button not found")
            return False
        await elem[0].click()
        # input("测试")
        await asyncio.sleep(5)

        comment_input = await page.J('div[class*="DivCommentContainer"]')
        print(comment_input)
        await comment_input.click()
        await page.keyboard.type(content)
        await asyncio.sleep(3)

        post = await page.xpath('//div[contains(text(), "Post")]')
        print(post)
        await post[0].click()

        await asyncio.sleep(3)
        await page.close()

        # comment_submit = await page.J('div[class*="post-container"]')
        # print(comment_submit)
        # await comment_submit.click()

    async def upload_video(self, video: str, title: str = "nice one", is_private: bool = False, page=None):
        # self.client.delete_cache_files()
        if not page:
            page: Page = await self.client.new_page(blocked_resources=[])

        page.setDefaultNavigationTimeout(0)
        if not os.path.exists(video):
            logger.error("Video file not found: {}".format(video))
            return False

        video = os.path.abspath(video)
        logger.debug("video file absolute path: {}".format(video))

        _ = await self.client.goto(f"/upload?lang=en", page=page, options={"waitUntil": "networkidle0"}, timeout=60000)

        time.sleep(10)
        elem = await page.JJ('input[name="upload-btn"]')
        print(elem)
        if not elem:
            print("video comment button not found")
            return False

        await elem[0].uploadFile(video)
        # input("测试")
        await asyncio.sleep(5)
        # disable
        # <button type="button" class="tiktok-btn-pc tiktok-btn-pc-large tiktok-btn-pc-primary tiktok-btn-pc-disabled">發佈</button>
        # enable
        # <button type="button" class="tiktok-btn-pc tiktok-btn-pc-large tiktok-btn-pc-primary">發佈</button>
        while True:
            button = await page.J('button[class*="tiktok-btn-pc-disabled"]')
            print("submit button ", button)
            if not button:
                logger.debug("submit button is enabled")
                break
            else:
                logger.debug("submit button is disabled")
                time.sleep(2)

        title_input = await page.J('div[class*="public-DraftStyleDefault-block"]')
        print(title_input)
        await title_input.click()
        await page.keyboard.type(title)
        await asyncio.sleep(3)

        button = await page.J('button[class*="tiktok-btn-pc-primary"]')
        print("submit: ", button)
        await button.click()
        await asyncio.sleep(3)

        return True

    async def message(self, username, message, page=None):
        if not page:
            page: Page = await self.client.new_page(blocked_resources=["media"])

        page.setDefaultNavigationTimeout(0)
        logger.info("Comment to: {username} message: {message}")
        # https://www.tiktok.com/@karenmanlangit?lang=en
        _ = await self.client.goto("/@{}?lang=en".format(username), page=page, options={"waitUntil": "networkidle0"}, timeout=60000)

        follow_title: str = await page.Jeval(
            ".follow-button",
            pageFunction="element => element.textContent",
        )

        logger.debug("follow title: |{}|".format(follow_title))
        if follow_title.lower() in ("follow", "关注", "關註", "關注"):
            logger.info(f"😏 {username} not follow")
            await page.click(".follow-button")
            time.sleep(2)

        await page.click(".message-button")
        time.sleep(5)

        while True:
            try:
                await page.click(".comment-input-inner-wrapper")
                break
            except pyppeteer.errors.PageError as e:
                print(e)
                time.sleep(2)
                continue

        time.sleep(1)
        await page.keyboard.type(message)

        time.sleep(2)
        await page.click(".send-button")
        
        return 