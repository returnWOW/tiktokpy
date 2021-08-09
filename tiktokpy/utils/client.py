from typing import List
import json

from tiktokpy.utils.logger import logger


async def block_resources_and_sentry(request, types: List[str]):
    is_blocked = False

    if request.resourceType in types:
        is_blocked = True

    if "/sentry/" in request.url:
        is_blocked = True

    if is_blocked:
        await request.abort()
    else:
        await request.continue_()


cnt = 0
async def catch_response_and_store(response, list_queue):
    global cnt
    if "/item_list" in response.url:
        cnt += 1
        logger.debug("get item list: {}".format(cnt))
        logger.debug("await: {}".format(cnt))
        data = await response.json()

        print(data)
        cnt_elem = 0
        for item in data["itemList"]:
            cnt_elem += 1
            list_queue.append(item)
        # logger.debug(f"🛒 Collected {len(data['items'])} items. Total: {cnt_elem}")
    else:
        # logger.debug("None {}".format(response.url))
        pass


async def catch_response_info(response, queue, url: str):
    if url in response.url:
        logger.debug(response.url)
        result = await response.json()

        await queue.put(result)
        logger.debug(f"🛒 Collected response: {result}")
