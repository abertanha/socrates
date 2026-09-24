"""Shared adversarial backends — the review's conditions as residents.

The fifth review found every data-destruction defect by simulating
conditions the happy paths never meet. Those conditions have homes now:

- reads that paginate — ``tiny_log_pages`` below: the backend's real
  pagination (2000 lines, no mark of its own truncation) at a size any
  log outgrows, so the whole-file readers walk windows on every read
- writes that fail — the losing-write backend inside
  ``tests/test_ask_answer_binding.py`` (the fresh log's write fails once)
- bytes that do not decode — the non-UTF-8 craft in the same file
- a directory squatting on a path — the sidecar squash in the same file

Scoped deliberately: only the answer-log's reads page here. The
engine's other readers still trust one read window — that is the
recorded maintenance item, not this fixture's business.
"""

from __future__ import annotations

import pytest
from deepagents.backends.filesystem import FilesystemBackend

from socrates.paths import ANSWERS_PATH


class TinyPages(FilesystemBackend):
    """Pages every read of ``paths`` at ``page`` lines; every other read
    keeps the backend's own default."""

    def __init__(self, root_dir, paths=(ANSWERS_PATH,), page=4, **kwargs):
        super().__init__(root_dir=root_dir, **kwargs)
        self._paths = paths
        self._page = page

    def read(self, file_path, offset=0, limit=2000):
        if file_path in self._paths:
            limit = self._page
        return super().read(file_path, offset=offset, limit=limit)


@pytest.fixture
def tiny_log_pages(tmp_path):
    """The answer log, read four lines at a window."""
    return TinyPages(tmp_path, virtual_mode=True)
