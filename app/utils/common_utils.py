"""
app/utils/common_utils.py
=====================
アプリケーション全体で使う共通ユーティリティ関数をまとめたモジュール
"""

import time
import string
from pathlib import Path
from zoneinfo import ZoneInfo

# 日本標準時タイムゾーン（UTC+9）
_JST = ZoneInfo("Asia/Tokyo")

def elapsed_ms(start: float) -> float:
    """
    計測開始時刻（time.time() の戻り値）からの経過時間をミリ秒で返す

    Args:
        start: 計測開始時刻（time.time() の戻り値）

    Returns:
        float: 経過時間（ミリ秒）
    """
    return round((time.time() - start) * 1000, 2)
