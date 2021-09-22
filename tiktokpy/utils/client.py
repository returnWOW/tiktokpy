from typing import List
import json

from tiktokpy.utils.logger import logger


async def block_resources_and_sentry(request, types: List[str]):
    is_blocked = False

    if request.resourceType in types:
        logger.debug("blocked: {}".format(request.resourceType))
        is_blocked = True

    if "/sentry/" in request.url:
        logger.debug("blocked: {}".format(request.url))
        is_blocked = True

    if is_blocked:
        await request.abort()
    else:
        await request.continue_()


cnt = 0
async def catch_response_and_store(res, list_queue, url_str="/item_list"):
    global cnt
    url = res.url
    if url_str in url:
        cnt += 1
        print("get item list: {} {}".format(cnt, url))
        # logger.debug("await: {}".format(cnt))
        data = await res.text()
        # logger.debug("data: {}".format(data))
        data = json.loads(data)

        # logger.debug("data_json: {}".format(data))
        cnt_elem = 0
        for item in data["itemList"]:
            cnt_elem += 1
            list_queue.append(item)
        print(f"🛒 Collected {len(data['items'])} items. Total: {cnt_elem}")
    else:
        # print("other url: {}".format(url))\
        pass


async def catch_response_info(response, queue, url: str):
    if url in response.url:
        logger.debug(response.url)
        result = await response.json()

        await queue.put(result)
        logger.debug(f"🛒 Collected response: {result}")
