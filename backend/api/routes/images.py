"""图片上传与读取。

粘贴的截图先上传落盘，拿到元信息后随记录一起提交 ——
真正的字节不进数据库，payload 里只留路径和尺寸。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ...core.config import get_settings
from ...domain.models import ImageAssetOut
from ...services.images import ImageStore

router = APIRouter(prefix="/images", tags=["images"])

# 单张上限，避免误粘贴超大图把磁盘写满
MAX_BYTES = 10 * 1024 * 1024


def get_store() -> ImageStore:
    settings = get_settings()
    settings.ensure_dirs()
    return ImageStore(settings)


@router.post("", response_model=ImageAssetOut, status_code=201)
async def upload(
    file: UploadFile = File(...),
    store: ImageStore = Depends(get_store),
) -> ImageAssetOut:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="空文件")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="图片超过 10MB")
    try:
        return store.save(data, file.content_type or "", file.filename or "")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{name}")
def read(name: str, store: ImageStore = Depends(get_store)) -> FileResponse:
    try:
        path = store.path_of(name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not path.exists():
        raise HTTPException(status_code=404, detail="图片不存在")
    return FileResponse(path)
