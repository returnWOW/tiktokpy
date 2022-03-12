import os
import json

import time
from dynaconf import loaders, settings

from tiktokpy.client import Client
from tiktokpy.utils.logger import logger
from tiktokpy.utils.settings import BASE_SETTINGS


class Login:
    def __init__(self, client) -> None:
        self.client: Client = client

    async def manual_login(self, username, password, cookie_file=None):
        # client = await Client.create(headless=False)
        client: Client = self.client
        page = await client.new_page()

        await client.goto("/login", page)
        await page.wait_for_selector('div[data-e2e="profile-icon"]', timeout=0)

        username = sub_title = None

        while not all((username, sub_title)):
            await page.hover('div[data-e2e="profile-icon"]')

            await page.wait_for_selector('ul[data-e2e="profile-popup"] > li:first-child')
            # going to "View profile" page
            await page.click('ul[data-e2e="profile-popup"] > li:first-child')

            await page.wait_for_selector('h2[data-e2e="user-title"]', timeout=0)

            username = await page.eval_on_selector(
                'h2[data-e2e="user-title"]',
                expression="element => element.textContent",
            )
            username = username.strip()

            sub_title = await page.eval_on_selector(
                'h1[data-e2e="user-subtitle"]',
                expression="element => element.textContent",
            )

        cookies = await client.context.cookies()

        # print(cookies)
        # logger.debug(cookies)
        loaders.write(
            f"{settings.HOME_DIR}/settings_test.toml",
            {**BASE_SETTINGS, **{"COOKIES": json.dumps(cookies), "USERNAME": username}},
            env="default",
        )

