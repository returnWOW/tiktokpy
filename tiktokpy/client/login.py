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

        # await client.stealth(page)

        await client.goto("/login", page)
        # await page.waitForXPath('//div[contains(text(), "TikTok")]', options={"timeout": 0})
        time.sleep(3)
        flag = False
        idx = 0
        while True:
            try:
                idx += 1
                print("check for login")
                elem = await page.xpath('//input[@autocomplete="reg_email__"]')
                print(elem)
                if not elem:
                    flag = False
                    break

                print("not login")
                if idx <= 10:
                    time.sleep(2)
                    print("recheck")
                    continue
                else:
                    break
                flag = True
            except Exception as e:
                logger.debug(e)
                flag = False 

        time.sleep(3)

        if flag:
            try:
                print("click phone button")
                use_phone = await page.Jx('//div[contains(text(), "使用者")]')
                await use_phone[0].click()

                time.sleep(1)

                use_pw = await page.Jx('//a[contains(text(), "使用密")]')
                print(use_pw)
                await use_pw[0].click()

                time.sleep(1)

                # await page.type('//input[@autocomplete="reg_email__"]', username, {'delay': 5})
                input_uname = await page.Jx('//input[@autocomplete="reg_email__"]')
                await input_uname[0].click()
                await page.keyboard.type(username)

                time.sleep(1)
                input_pw = await page.Jx('//input[@type="password"]')
                await input_pw[0].click()
                await page.keyboard.type(password)

                input("Enter for confirm")

                logger.info(f"🔑 Logged as @{username}")
                cookies = await page.cookies()

                if not cookie_file:
                    cookie_file = os.path.join("cookies", "{}_cookie.json".format(username))

                with open(cookie_file, "w", encoding="utf-8") as fout:
                    json.dump(cookies, fout)
            except IndexError as e:
                logger.error("already login：{}".format(e))
        else:
            print("already login, no need relogin")
            cookies = await page.cookies()

        # print(cookies)
        # logger.debug(cookies)
        loaders.write(
            f"{settings.HOME_DIR}/settings.toml",
            {**BASE_SETTINGS, **{"COOKIES": json.dumps(cookies), "USERNAME": username}},
            env="default",
        )

