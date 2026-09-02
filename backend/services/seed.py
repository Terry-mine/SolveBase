"""把 config/vocab.yaml 灌进 vocab 表。

改完词表执行：`python -m backend.cli seed`
"""

from __future__ import annotations

import sqlite3

from ..db.repositories.jobs import VocabRepository
from ..domain.vocab import audit, get_vocabulary


def seed_vocabulary(conn: sqlite3.Connection) -> dict:
    vocab = get_vocabulary()
    issues = audit(vocab)
    rows = VocabRepository(conn).replace_all(vocab.all_rows())

    return {
        "vocab_version": vocab.version,
        "types": [
            {
                "key": key,
                "label": spec.label,
                "statuses": spec.status_codes,
                "categories": spec.category_codes,
            }
            for key, spec in vocab.types.items()
        ],
        "rows_written": rows,
        "issues": [{"level": i.level, "message": i.message} for i in issues],
    }
