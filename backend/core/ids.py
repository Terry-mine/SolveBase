"""ID 与时间。

UUIDv7：前 48 位是毫秒时间戳，天然按时间有序。
对增量同步很关键 —— `WHERE updated_at > cursor` 和按 id 排序结果一致，
分页和断点续传都不会漏数据。
"""

from __future__ import annotations

import os
import time
import uuid


def uuid7() -> str:
    """生成 UUIDv7 字符串。"""
    ms = int(time.time() * 1000) & 0xFFFF_FFFF_FFFF
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF
    rand_b = int.from_bytes(os.urandom(8), "big") & 0x3FFF_FFFF_FFFF_FFFF
    value = (ms << 80) | (0x7 << 76) | (rand_a << 64) | (0b10 << 62) | rand_b
    return str(uuid.UUID(int=value))


def now_ms() -> int:
    """当前毫秒时间戳。统一走这个函数，方便测试时注入固定时间。"""
    return int(time.time() * 1000)


def new_id() -> str:
    return uuid7()
