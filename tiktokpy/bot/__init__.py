import os
import typing
from datetime import datetime
from types import TracebackType
from typing import List, Optional

import humanize
from dynaconf import settings

from tiktokpy.client import Client
from tiktokpy.client import user
from tiktokpy.client.login import Login
from tiktokpy.client.trending import Trending
from tiktokpy.client.user import User
from tiktokpy.models.feed import FeedItem, FeedItems
from tiktokpy.utils.logger import init_logger, logger
from tiktokpy.utils.settings import load_or_create_settings

from .version import __version__


class TikTokPy:
    def __init__(self, settings_path: Optional[str] = None, proxy: Optional[str] = "http://127.0.0.1:1080", username=None, pw=None, cookie_path="cookies"):
        init_logger()
        self.started_at = datetime.now()
        self.client: Client
        self.proxy = proxy
        self.username = username
        self.pw = pw
        self.userdata_dir = "userdata"
        self.cookie_path = os.path.join(cookie_path, "{}_cookie.json".format(self.username))

        logger.info("🥳 TikTokPy initialized. Version: {}", __version__)

        load_or_create_settings(path=settings_path)
        self.one_page = None

        if settings.get("COOKIES") and settings.get("USERNAME"):
            logger.info(f"✅ Used cookies of @{settings.USERNAME}")
        else:
            logger.info("🛑 Cookies not found, anonymous mode")

    async def __aenter__(self):
        await self.init_bot()

        return self

    async def __aexit__(
        self,
        exc_type: typing.Type[BaseException] = None,
        exc_value: BaseException = None,
        traceback: TracebackType = None,
    ) -> None:
        logger.debug("🤔Trying to close browser..")

        await self.client.browser.close()

        logger.debug("✋ Browser successfully closed")
        logger.info(
            "✋ TikTokPy finished working. Session lasted: {}",
            humanize.naturaldelta(datetime.now() - self.started_at),
        )

    async def trending(self, amount: int = 50, lang: str = "en") -> List[FeedItem]:
        logger.info("📈 Getting trending items")
        items = await Trending(client=self.client).feed(amount=amount, lang=lang, page=self.one_page)

        logger.info(f"📹 Found {len(items)} videos")
        # print()
        _trending = FeedItems(__root__=items)

        return _trending.__root__

    async def search(self, amount: int = 50, lang: str = "en", kw="nike", dbSession=None, dbobj=None, kwdbobj=None) -> List[FeedItem]:
        logger.info("📈 Getting trending items")
        items = await Trending(client=self.client).search(amount=amount, lang=lang, page=self.one_page, kw=kw, 
                                                          dbSession=dbSession, dbobj=dbobj, kwdbobj=kwdbobj)

        logger.info(f"📹 Found {len(items)} videos")

        return items

    async def get_comments(self, username: str, media_id: int, amount: int = 50, dbSession=None, dbobj=None) -> List:
        logger.info("📈 Getting media {media_id} comments items")
        items = await User(client=self.client).get_comments(username, media_id, amount=amount, page=self.one_page,
                                                            dbSession=dbSession, dbobj=dbobj)

        logger.info(f"📹 Found {len(items)} comments")

        return items

    async def comment(self, username: str, media_id: int, content="nice") -> List:
        logger.info("📈 Comment with media {media_id} content: {content}")
        await User(client=self.client).comment(username, media_id, content=content, page=self.one_page)

    async def message_to(self, username: str, message: str="Hello") -> List:
        logger.info("📈 Comment with media {media_id} content: {content}")
        await User(client=self.client).message(username, message, page=self.one_page)

    async def upload_video(self,  video: str, title: str = "nice one", is_private: bool = False,) -> List:
        logger.info("📈 Comment with media {media_id} content: {content}")
        res = await User(client=self.client).upload_video( video, title = title, is_private = is_private, page=self.one_page)
        return res

    async def follow(self, username: str):
        username = f"@{username.lstrip('@')}"
        await User(client=self.client).follow(username=username, page=self.one_page)

    async def like(self, feed_item: FeedItem):
        await User(client=self.client).like(
            username=feed_item.author.username,
            video_id=feed_item.id,
            page=self.one_page
        )

    async def unlike(self, feed_item: FeedItem):
        await User(client=self.client).unlike(
            username=feed_item.author.username,
            video_id=feed_item.id,
        )

    async def unfollow(self, username: str):
        username = f"@{username.lstrip('@')}"
        await User(client=self.client).unfollow(username=username)

    async def login_session(self):
        if not self.username or not self.pw:
            logger.error("Username or pw is none")
            return False

        await Login(client=self.client).manual_login(self.username, self.pw, cookie_file=self.cookie_path)
        return True

    async def user_feed(self, username: str, amount: int = 50) -> List[FeedItem]:
        username = f"@{username.lstrip('@')}"
        logger.info(f"📈 Getting {username} feed")
        items = await User(client=self.client).feed(username=username, amount=amount, page=self.one_page)

        logger.info(f"📹 Found {len(items)} videos")
        feed = FeedItems(__root__=items)

        return feed.__root__

    async def init_bot(self):
        if not os.path.exists(self.userdata_dir):
            os.mkdir(self.userdata_dir)
            
        userdata_dir = os.path.join(self.userdata_dir, self.username)
        self.client: Client = await Client.create(headless=False, proxy=self.proxy, userdata=userdata_dir)
        # if not self.one_page:
            # self.one_page = await self.client.new_page(blocked_resources=["media", "image", "font"])

    @classmethod
    async def create(cls):
        self = TikTokPy()
        await self.init_bot()

        return self

    async def screenshot(self, page, name=""):
        filename = f"{name}_{datetime.now()}".lstrip("_")

        await self.client.screenshot(
            path=f"{settings.HOME_DIR}/screenshots/{filename}.png",
            page=page,
        )
