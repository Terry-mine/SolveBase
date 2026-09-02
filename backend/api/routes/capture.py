"""速记入口。

整个系统能否活下去，取决于这个接口有多省事：
只要求一个 text 字段，其余全部后端推断。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ...domain.models import CaptureIn, CaptureOut
from ...services.capture import CaptureService
from ..deps import get_capture_service

router = APIRouter(prefix="/capture", tags=["capture"])


@router.post("", response_model=CaptureOut, status_code=201)
def capture(payload: CaptureIn, service: CaptureService = Depends(get_capture_service)) -> CaptureOut:
    return service.capture(payload)
