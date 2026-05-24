"""
app/utils/logger.py
アプリケーション共通ロガーを提供する。
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from app.config import settings

def get_logger(name: str) -> logging.Logger:
    """
    名前付きロガーを返す。初回呼び出し時にハンドラを設定する。

    Args:
        name: ロガー名（通常は __name__ を渡す）

    Returns:
        logging.Logger: ハンドラ設定済みのロガー

    Example:
        logger = get_logger(__name__)
        logger.info("処理開始")
    """
    logger = logging.getLogger(name)

    # すでにハンドラが設定済みならそのまま返す（二重登録を防ぐ）
    if logger.handlers:
        return logger

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # ルートロガーへの伝播を止める
    # → uvicorn がルートロガーにハンドラを追加していても二重出力にならない
    logger.propagate = False

    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --- ファイルハンドラ（ローテーションなし・logrotateに任せる）---
    os.makedirs(settings.LOG_DIR, exist_ok=True)
    file_handler = logging.FileHandler(
        filename=os.path.join(settings.LOG_DIR, settings.LOG_FILENAME),
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # --- コンソールハンドラ（開発時確認用。不要なら削除可）---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger
