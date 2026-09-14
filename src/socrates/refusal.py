"""The engine's structured refusal — ordering as information (ticket 29).

The ordering prose retired from the skill lives here now: when a verb is
called in the wrong order, the engine refuses with the reason and the
admissible next verbs, as data the conductor reads and repairs. A
``Refusal`` IS-A ``ValueError`` — every existing gate, catch, and pin
keeps working; the payload just gained its second field.
"""

from __future__ import annotations


class Refusal(ValueError):
    """A wrong-order refusal: the reason and the admissible next verbs.

    ``admissible`` lists the engine verbs the conductor may call next —
    verb names as the invocation files name them. It is information for
    the conductor's next move, never enforcement of its own.
    """

    def __init__(self, reason: str, admissible: list[str]) -> None:
        super().__init__(reason)
        self.reason = reason
        self.admissible = list(admissible)
