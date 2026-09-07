"""速记入口。

整个系统能否活下去，取决于这个接口有多省事：
只要求一个 text 字段，其余全部后端推断。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ...domain.models import CaptureIn, CaptureOut
from ...services.capture import CaptureService
from ..deps import get_capture_service

router = APIRouter(prefix="/capture", tags=["capture"])


@router.post("", response_model=CaptureOut, status_code=201)
def capture(payload: CaptureIn, service: CaptureService = Depends(get_capture_service)) -> CaptureOut:
    try:
        return service.capture(payload)
    except ValueError as exc:
        # 缺 title 这类属于用户输入问题，给 400，别让它冒成 500
        raise HTTPException(status_code=400, detail=str(exc)) from exc
