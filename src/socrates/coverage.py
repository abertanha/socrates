"""Coverage-driven exploration budget (ADR-0004).

Coverage is read pass-over-pass from declining Conflict signals. The per-pass
recursion limit scales inversely with Coverage — an exploration allowance,
never a quality gate (ADR-0002). Chosen limits must be stamped onto subagent
invokes so they do not silently fall back to 25 (deepagents #1698).
"""

from __future__ import annotations

import json
from typing import Any

from deepagents.backends.protocol import BackendProtocol
from langchain_core.runnables import Runnable, RunnableConfig

from socrates.paths import COVERAGE_PATH

# Silent LangGraph / deepagents fallback — must not be the selected budget
# when exploration is warranted (#1698).
SILENT_SUBAGENT_FALLBACK = 25

# Exploration allowance bounds (Relevance Filter still anchors Scenarios).
RECURSION_LIMIT_GENEROUS = 200  # low Coverage — sparse, early
RECURSION_LIMIT_LEAN = 40  # high Coverage — mature


def measure_coverage(conflicts_per_pass: dict[str, int] | list[int]) -> float:
    """0.0 = sparse/early; 1.0 = mature. Declining conflicts → rising Coverage."""
    if isinstance(conflicts_per_pass, dict):
        if not conflicts_per_pass:
            return 0.0
        counts = [conflicts_per_pass[k] for k in sorted(conflicts_per_pass, key=int)]
    else:
        counts = list(conflicts_per_pass)
    if not counts:
        return 0.0
    peak = max(counts)
    if peak <= 0:
        return 1.0
    return max(0.0, min(1.0, 1.0 - (counts[-1] / peak)))


def recursion_limit_for(coverage: float) -> int:
    """Select recursion_limit ∝ 1/Coverage (generous when sparse, lean when dense)."""
    c = max(0.0, min(1.0, float(coverage)))
    return int(
        round(
            RECURSION_LIMIT_LEAN
            + (RECURSION_LIMIT_GENEROUS - RECURSION_LIMIT_LEAN) * (1.0 - c)
        )
    )


class CoverageStore:
    """Persists Coverage signals and the selected exploration budget."""

    def __init__(self, backend: BackendProtocol) -> None:
        self._backend = backend

    def add_conflicts(self, pass_no: int, count: int) -> None:
        if count <= 0:
            return
        data = self._load()
        by_pass = data.setdefault("conflicts_per_pass", {})
        key = str(pass_no)
        by_pass[key] = int(by_pass.get(key, 0)) + count
        self._save(data)

    def measure(self) -> float:
        return measure_coverage(self._load().get("conflicts_per_pass", {}))

    def select_budget(self) -> dict[str, Any]:
        """Compute Coverage and persist the inverse exploration allowance."""
        data = self._load()
        coverage = measure_coverage(data.get("conflicts_per_pass", {}))
        limit = recursion_limit_for(coverage)
        data.update(
            {
                "coverage": coverage,
                "recursion_limit": limit,
                "role": "exploration_allowance",
                "quality_gate": False,
                "relevance_anchored": True,
                "subagent_propagations": data.get("subagent_propagations", []),
            }
        )
        self._save(data)
        return {
            "coverage": coverage,
            "recursion_limit": limit,
            "conflicts_per_pass": data.get("conflicts_per_pass", {}),
            "role": "exploration_allowance",
            "quality_gate": False,
            "relevance_anchored": True,
        }

    def ensure_budget(self) -> dict[str, Any]:
        data = self._load()
        if data.get("recursion_limit") is None:
            return self.select_budget()
        return {
            "coverage": data.get("coverage", self.measure()),
            "recursion_limit": data["recursion_limit"],
            "conflicts_per_pass": data.get("conflicts_per_pass", {}),
            "role": data.get("role", "exploration_allowance"),
            "quality_gate": bool(data.get("quality_gate", False)),
            "relevance_anchored": bool(data.get("relevance_anchored", True)),
        }

    def current_recursion_limit(self) -> int:
        return int(self.ensure_budget()["recursion_limit"])

    def record_propagation(self, subagent_name: str, recursion_limit: int) -> None:
        """Record that a subagent invoke received the chosen limit (#1698)."""
        data = self._load()
        props = data.setdefault("subagent_propagations", [])
        props.append(
            {
                "subagent": subagent_name,
                "recursion_limit": recursion_limit,
                "silent_fallback_avoided": recursion_limit != SILENT_SUBAGENT_FALLBACK,
            }
        )
        data["last_subagent_recursion_limit"] = recursion_limit
        self._save(data)

    def snapshot(self) -> dict[str, Any]:
        return self._load()

    def _load(self) -> dict[str, Any]:
        result = self._backend.read(COVERAGE_PATH)
        if result.error or result.file_data is None:
            return {
                "conflicts_per_pass": {},
                "subagent_propagations": [],
            }
        content = result.file_data["content"]
        if not content.strip():
            return {
                "conflicts_per_pass": {},
                "subagent_propagations": [],
            }
        return json.loads(content)

    def _save(self, data: dict[str, Any]) -> None:
        self._backend.write(COVERAGE_PATH, json.dumps(data, indent=2))


class BudgetAwareSubagent(Runnable):
    """CompiledSubAgent wrapper that stamps Coverage-selected recursion_limit.

    Prevents the silent fallback to 25 (deepagents #1698) by always applying
    the exploration budget from the Coverage store on invoke.
    """

    def __init__(
        self,
        inner: Runnable,
        backend: BackendProtocol,
        subagent_name: str,
    ) -> None:
        super().__init__()
        self._inner = inner
        self._backend = backend
        self._subagent_name = subagent_name

    def invoke(
        self,
        input: Any,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> Any:
        store = CoverageStore(self._backend)
        limit = store.current_recursion_limit()
        merged: RunnableConfig = {**(config or {}), "recursion_limit": limit}
        result = self._inner.invoke(input, merged, **kwargs)
        return self._with_propagation_recorded(result, store, limit)

    async def ainvoke(
        self,
        input: Any,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> Any:
        store = CoverageStore(self._backend)
        limit = store.current_recursion_limit()
        merged: RunnableConfig = {**(config or {}), "recursion_limit": limit}
        result = await self._inner.ainvoke(input, merged, **kwargs)
        return self._with_propagation_recorded(result, store, limit)

    def _with_propagation_recorded(
        self,
        result: Any,
        store: CoverageStore,
        limit: int,
    ) -> Any:
        """Merge propagation into returned ``files`` so the parent Command keeps it.

        Recording via StateBackend during the wrapper races the subagent's
        returned file snapshot, which would overwrite the parent Coverage file.
        """
        from deepagents.backends.utils import create_file_data, file_data_to_string, update_file_data

        if not isinstance(result, dict):
            return result
        files = dict(result.get("files") or {})
        existing = files.get(COVERAGE_PATH)
        if existing is not None:
            base = json.loads(file_data_to_string(existing))
        else:
            base = store.snapshot()
        props = list(base.get("subagent_propagations", []))
        props.append(
            {
                "subagent": self._subagent_name,
                "recursion_limit": limit,
                "silent_fallback_avoided": limit != SILENT_SUBAGENT_FALLBACK,
            }
        )
        base["subagent_propagations"] = props
        base["last_subagent_recursion_limit"] = limit
        base.setdefault("recursion_limit", limit)
        content = json.dumps(base, indent=2)
        files[COVERAGE_PATH] = (
            update_file_data(existing, content)
            if existing is not None
            else create_file_data(content)
        )
        return {**result, "files": files}



def exploration_invoke_config(
    thread_id: str,
    *,
    recursion_limit: int | None = None,
    files: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Invoke config carrying the Coverage-selected recursion_limit for this pass."""
    limit = recursion_limit
    if limit is None and files is not None and COVERAGE_PATH in files:
        snapshot = json.loads(files[COVERAGE_PATH]["content"])
        limit = int(snapshot["recursion_limit"])
    if limit is None:
        limit = RECURSION_LIMIT_GENEROUS
    return {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": limit,
    }
