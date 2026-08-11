"""Notification policy — quiet by default (CONTEXT / ADR-0002).

Routine Probes and Interviews are not Notifications. Only two triggers:
unavoidable Conflicts (non-deferrable, block progress) and Supersede cascades.
Delivery channels (push, email, in-app) are stubbed behind this boundary.
"""

from __future__ import annotations

import json
from typing import Any, Protocol

from deepagents.backends.protocol import BackendProtocol

from socrates.paths import NOTIFICATIONS_PATH

ALLOWED_KINDS = frozenset({"unavoidable_conflict", "supersede_cascade"})
CHANNEL_NAMES = ("in_app", "push", "email")


class DeliveryChannel(Protocol):
    """Delivery is an implementation detail — stubbed for the harness."""

    name: str

    def deliver(self, notification: dict[str, Any]) -> dict[str, Any]:
        """Deliver a Notification; returns a delivery receipt."""


class StubDeliveryChannel:
    """Records deliveries without contacting a real push/email/in-app service."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.deliveries: list[dict[str, Any]] = []

    def deliver(self, notification: dict[str, Any]) -> dict[str, Any]:
        receipt = {
            "channel": self.name,
            "status": "stubbed",
            "notification_kind": notification.get("kind"),
            "notification_id": notification.get("id"),
        }
        self.deliveries.append(receipt)
        return receipt


def is_unavoidable(conflict_level: str, *, critical: bool) -> bool:
    """Non-deferrable Conflict that blocks progress until resolved.

    L4 (Accepted × Accepted) leaves the Model inconsistent — Iteration (or
    other resolution) is required; parking it would block modeling progress.
    """
    return critical and conflict_level == "L4"


def default_channels() -> dict[str, StubDeliveryChannel]:
    return {name: StubDeliveryChannel(name) for name in CHANNEL_NAMES}


class NotificationService:
    """Quiet-by-default Notification boundary with stubbed delivery channels."""

    def __init__(
        self,
        backend: BackendProtocol,
        *,
        channels: dict[str, DeliveryChannel] | None = None,
    ) -> None:
        self._backend = backend
        self._channels: dict[str, DeliveryChannel] = channels or default_channels()

    def emit(self, kind: str, **payload: Any) -> dict[str, Any]:
        """Persist and stub-deliver a policy-allowed Notification."""
        if kind not in ALLOWED_KINDS:
            raise ValueError(
                f"Quiet by default: Notification kind {kind!r} is not allowed; "
                f"only {sorted(ALLOWED_KINDS)} may interrupt outside Interview flow"
            )
        notes = self.list_notifications()
        notification: dict[str, Any] = {
            "id": f"n{len(notes) + 1}",
            "kind": kind,
            **payload,
        }
        deliveries = [
            channel.deliver(notification) for channel in self._channels.values()
        ]
        notification["deliveries"] = deliveries
        notes.append(notification)
        self._backend.write(
            NOTIFICATIONS_PATH,
            json.dumps({"notifications": notes}, indent=2),
        )
        return notification

    def list_notifications(self) -> list[dict[str, Any]]:
        result = self._backend.read(NOTIFICATIONS_PATH)
        if result.error or result.file_data is None:
            return []
        content = result.file_data["content"]
        if not content.strip():
            return []
        raw = json.loads(content)
        return list(raw.get("notifications", []))

    def channel_names(self) -> tuple[str, ...]:
        return tuple(self._channels.keys())
