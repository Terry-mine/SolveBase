"""词表查询。

前端的下拉选项全部从这里取，不硬编码 —— 改完 vocab.yaml 执行一次
`python -m backend.cli seed` 后刷新页面即可生效。
"""

from __future__ import annotations

from fastapi import APIRouter

from ...domain.vocab import audit, get_vocabulary

router = APIRouter(prefix="/vocab", tags=["vocab"])


@router.get("")
def get_vocab() -> dict:
    vocab = get_vocabulary()
    return {
        "version": vocab.version,
        "common_statuses": [{"code": s.code, "label": s.label} for s in vocab.common_statuses],
        "types": [
            {
                "key": key,
                "label": spec.label,
                "desc": spec.desc,
                "statuses": [
                    {"code": s.code, "label": s.label, "desc": s.desc} for s in spec.statuses
                ],
                "categories": [
                    {"code": c.code, "label": c.label, "desc": c.desc} for c in spec.categories
                ],
            }
            for key, spec in vocab.types.items()
        ],
        "issues": [{"level": i.level, "message": i.message} for i in audit(vocab)],
    }
