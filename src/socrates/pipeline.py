"""Modeling Activity pipeline — precedence and FS progress tracking."""

from __future__ import annotations

import json
from typing import Any, Literal

from deepagents.backends.protocol import BackendProtocol

from socrates.paths import PIPELINE_PATH

ModelingActivity = Literal[
    "requirements",
    "domain_modeling",
    "behavioral_specification",
]

ACTIVITIES_IN_ORDER: tuple[ModelingActivity, ...] = (
    "requirements",
    "domain_modeling",
    "behavioral_specification",
)

# deepagents `task` subagent_type values (kebab-case).
ACTIVITY_SUBAGENT_TYPE: dict[ModelingActivity, str] = {
    "requirements": "requirements",
    "domain_modeling": "domain-modeling",
    "behavioral_specification": "behavioral-specification",
}

SUBAGENT_TYPE_TO_ACTIVITY: dict[str, ModelingActivity] = {
    v: k for k, v in ACTIVITY_SUBAGENT_TYPE.items()
}


class PipelineStore:
    """Tracks Modeling Activity precedence on the virtual filesystem."""

    def __init__(self, backend: BackendProtocol) -> None:
        self._backend = backend

    def begin(self, activity: ModelingActivity) -> None:
        data = self._load()
        if data.get("active") == activity:
            return
        expected_index = len(data["completed"])
        if expected_index >= len(ACTIVITIES_IN_ORDER):
            raise ValueError("All Modeling Activities are already completed")
        expected = ACTIVITIES_IN_ORDER[expected_index]
        if activity != expected:
            raise ValueError(
                f"Modeling Activity precedence violated: expected '{expected}', "
                f"got '{activity}'"
            )
        if data.get("active") is not None and data["active"] != activity:
            raise ValueError(
                f"Activity '{data['active']}' is still active; "
                f"complete it before starting '{activity}'"
            )
        data["active"] = activity
        self._save(data)

    def complete(self, activity: ModelingActivity) -> None:
        data = self._load()
        if data.get("active") != activity:
            raise ValueError(
                f"Cannot complete '{activity}'; active activity is {data.get('active')!r}"
            )
        data["completed"].append(activity)
        data["active"] = None
        self._save(data)

    def snapshot(self) -> dict[str, Any]:
        return self._load()

    def _load(self) -> dict[str, Any]:
        result = self._backend.read(PIPELINE_PATH)
        if result.error or result.file_data is None:
            return {"completed": [], "active": None}
        content = result.file_data["content"]
        if not content.strip():
            return {"completed": [], "active": None}
        return json.loads(content)

    def _save(self, data: dict[str, Any]) -> None:
        self._backend.write(PIPELINE_PATH, json.dumps(data, indent=2))
