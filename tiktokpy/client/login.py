import os
import json
from re import sub

import time
import playwright
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
    
    async def check_login(self, page):
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
        return all(username, sub_title)

    async def manual_login2(self, uname, pw, cookie_file=None):
        # client = await Client.create(headless=False)
        client: Client = self.client
        page = await client.new_page()
        print("go login")
        await client.goto("/login", page)
        print("login page")
        # await page.wait_for_selector('div[data-e2e="profile-icon"]', timeout=0)

        time.sleep(5)
        username = uname
        sub_title = None
        idx = 0
        flag = False
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
            print(username, sub_title)
            idx += 1

        if flag:
            try:
                print("click phone button")
                use_phone = page.locator('xpath=//div[contains(text(), "Use phone")]')
                await use_phone.click()
                time.sleep(1)

                use_pw = page.locator('xpath=//a[contains(text(), "Log in with password")]')
                print(use_pw)
                await use_pw.click()

                time.sleep(1)

                # await page.type('//input[@autocomplete="reg_email__"]', username, {'delay': 5})
                input_uname = page.locator('xpath=//input[@autocomplete="reg_email__"]')
                await input_uname.click()
                await page.keyboard.type(uname)

                time.sleep(1)
                input_pw = page.locator('xpath=//input[@type="password"]')
                await input_pw.click()
                await page.keyboard.type(pw)

                input("Enter for confirm")

                logger.info(f" Logged as @{username}")
                cookies = await client.context.cookies()

            except IndexError as e:
               logger.error("already login?: {}".format(e))
        else:
            print("already login, no need relogin")
            cookies = await client.context.cookies()

        if not cookie_file:
            cookie_file = os.path.join("cookies", "{}_cookie.json".format(uname))

        with open(cookie_file, "w", encoding="utf-8") as fout:
            json.dump(cookies, fout)

        # print(cookies)
        # logger.debug(cookies)
        loaders.write(
            f"{settings.HOME_DIR}/settings.toml",
            {**BASE_SETTINGS, **{"COOKIES": json.dumps(cookies), "USERNAME": username}},
            env="default",
        ) 