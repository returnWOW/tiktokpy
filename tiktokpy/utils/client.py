from typing import List
import re
import json
import datetime

from tiktokpy.utils.logger import logger

import emoji


def get_dt_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def check_num_and_alpha(chs):
    for uchar in chs:
        if not ((uchar >= u'\u0030' and uchar <= u'\u0039') 
           or ((uchar >= u'\u0041' and uchar<=u'\u005a') 
           or (uchar >= u'\u0061' and uchar<=u'\u007a'))):
            return False
        
    return True


def trans_char(s):

    s = emoji.demojize(s.replace("'", " ").replace("\n", " "))

    s = re.sub(r"\\u.{4}", '', s.__repr__())

    s = s.replace("'", " ").replace("\n", " ")

    s.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    return s


def get_media_desc_tags(desc, logger=None):
    tags = []
    if logger: logger.debug("处理tag {}".format(desc))
    
    len_total = len(desc)
    start_idx = 0
    len_word = 0
    start_sign = False

    while start_idx < len_total:
        if desc[start_idx] == "#" and not start_sign:
            start_sign = True
            start_idx += 1
        elif start_sign:
            len_word += 1
            if start_idx + len_word > len_total - 1:
                tags.append(desc[start_idx:].lower())
                break

            if desc[start_idx + len_word] in (" ", "\n", "#", "\xa0") or start_idx + len_word == len_word - 1:
                if len_word < 100:
                    # logger.debug(desc[start_idx: start_idx + len_word])
                    tags.append(desc[start_idx: start_idx + len_word].lower())
                start_idx += len_word
                len_word = 0
                start_sign = False
        else:
            start_idx += 1

    logger.info("获取到搜索词：{}".format(len(tags)))
    return tags



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
async def catch_response_and_store(res, list_queue, url_str="/item_list", key="itemList"):
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
        for item in data[key]:
            cnt_elem += 1
            list_queue.append(item)
        print(f"🛒 Collected {len(data['items'])} items. Total: {cnt_elem}")
    else:
        # print("other url: {}".format(url))
        pass

    await res.continue_()


async def catch_response_info(response, queue, url: str):
    if url in response.url:
        logger.debug(response.url)
        result = await response.json()

        await queue.put(result)
        logger.debug(f"🛒 Collected response: {result}")
