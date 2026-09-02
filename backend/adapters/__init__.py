"""导入本包即完成所有 provider 的自注册。

新增 adapter 文件后，在这里加一行 import 即可（这是唯一需要动的地方）。
"""

from .embedding import noop as _embedding_noop  # noqa: F401
from .llm import noop as _llm_noop  # noqa: F401
from .reranker import noop as _reranker_noop  # noqa: F401
from .sync import noop as _sync_noop  # noqa: F401

__all__ = ["_embedding_noop", "_llm_noop", "_reranker_noop", "_sync_noop"]
