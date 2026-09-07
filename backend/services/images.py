"""图片资产存储。

截图落盘到 data/assets/images/，数据库只存元信息（路径 + 尺寸 + OCR 状态）。
这样安排有三个好处：

- 数据库不会被 base64 撑爆（一张截图转 base64 能到几百 KB）
- 后续接 OCR 时，可以直接按路径读原图，不用先解 base64
- 将来换存储（本地磁盘 → 对象存储）只需要替换这一个模块

OCR 目前不实现，但 asset 里已带 ocr 字段，接的时候不用改数据形状。
"""

from __future__ import annotations

import uuid
from pathlib import Path

from ..core.config import Settings
from ..domain.models import ImageAssetOut, ImageOcr

# 允许的图片类型，挡掉误粘贴的非图片文件
_ALLOWED = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
}


def _ext(mime: str, filename: str) -> str:
    """优先按 mime 定扩展名；mime 不可信时退回原文件名后缀。"""
    if mime in _ALLOWED:
        return _ALLOWED[mime]
    suffix = Path(filename or "").suffix.lower()
    return suffix if suffix in _ALLOWED.values() else ".png"


class ImageStore:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        base = settings.assets_dir or (settings.data_dir / "assets")
        self.root = base / "images"
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, data: bytes, mime: str, filename: str) -> ImageAssetOut:
        """落盘一张图，返回它的元信息。"""
        looks_like_image = mime in _ALLOWED or (filename or "").lower().endswith(
            tuple(_ALLOWED.values())
        )
        if not looks_like_image:
            raise ValueError(f"不支持的图片类型：{mime or filename or '未知'}")

        name = f"{uuid.uuid4().hex}{_ext(mime, filename)}"
        (self.root / name).write_bytes(data)

        return ImageAssetOut(
            id=uuid.uuid4().hex,
            filename=name,
            url=f"{self.settings.api_prefix}/images/{name}",
            mime=mime or "image/png",
            size=len(data),
            ocr=ImageOcr(),
        )

    def path_of(self, name: str) -> Path:
        """解析出磁盘路径。挡掉 ../ 之类的路径穿越。"""
        target = (self.root / name).resolve()
        if not str(target).startswith(str(self.root.resolve())):
            raise ValueError("非法的图片路径")
        return target
