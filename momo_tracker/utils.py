import datetime
import re
from typing import List, Optional, TypeVar

import aiohttp


def extract_url(text: str) -> Optional[str]:
    pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    match = re.search(pattern, text)
    if match:
        return match.group()
    else:
        return None


T = TypeVar("T")


def split_list(input_list: List[T], n: int) -> List[List[T]]:
    """
    Split a list into sublists of length n

    Parameters:
        input_list: The input list
        n: The length of each sublist
    """
    if n <= 0:
        raise ValueError("Parameter n must be a positive integer")

    return [input_list[i : i + n] for i in range(0, len(input_list), n)]


async def line_notify(token: str, message: str) -> bool:
    headers = {"Authorization": f"Bearer {token}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            await session.post(
                "https://notify-api.line.me/api/notify", data={"message": message}
            )
        except Exception:
            return False
        else:
            return True


def get_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
