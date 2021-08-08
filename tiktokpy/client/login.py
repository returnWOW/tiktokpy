import json

import time
from dynaconf import loaders, settings

from tiktokpy.client import Client
from tiktokpy.utils.logger import logger
from tiktokpy.utils.settings import BASE_SETTINGS


class Login:
    def __init__(self, client) -> None:
        self.client = client

    async def manual_login(self, username, password):
        # client = await Client.create(headless=False)
        client = self.client
        page = await client.new_page()

        await client.stealth(page)

        await client.goto("/login", page)
        await page.waitForSelector(".menu-right .profile", options={"timeout": 0})

        username = sub_title = None

        use_phone = await page.Jx('//div[contains(text(), "使用电话")]')
        await use_phone.click()

        time.sleep(0.5)

        use_pw = await page.Jx('//a[contains(text(), "使用密码登陆")]')
        await use_pw.click()

        time.sleep(0.5)

        input_uname = await page.Jx('//input[@autocomplete="reg_email__"]')
        await input_uname.send_keys(username)

        input_pw = await page.Jx('//input[@type="password"]')
        await input_pw.send_keys(password)

        # while not all((username, sub_title)):
        #     await page.hover(".menu-right .profile")

        #     await page.waitFor(".profile-actions > li:first-child")
        #     # going to "View profile" page
        #     await page.click(".profile-actions > li:first-child")

        #     try:
        #         await page.waitForSelector(".share-title", options={"timeout": 10_000})
        #     except Exception:
        #         continue

        #     username = await page.Jeval(
        #         ".share-title",
        #         pageFunction="element => element.textContent",
        #     )
        #     username = username.strip()

        #     sub_title = await page.Jeval(
        #         ".share-sub-title",
        #         pageFunction="element => element.textContent",
        #     )
        input("点击登陆")

        logger.info(f"🔑 Logged as @{username} aka {sub_title}")

        cookies = await page.cookies()

        loaders.write(
            f"{settings.HOME_DIR}/settings.toml",
            {**BASE_SETTINGS, **{"COOKIES": json.dumps(cookies), "USERNAME": username}},
            env="default",
        )

        await client.browser.close()
