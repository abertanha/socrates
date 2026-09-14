"""The invocation runner — the one place JSON meets transport (ticket 29).

An invocation file is thin by construction: parse, one engine call,
serialize. All of the transport lives here — ``--root`` selects the
session directory (the state rides on real disk, so a closed terminal
never ends the session), the JSON payload arrives as one argument or on
stdin, and every exit is a JSON object: never a stack trace. Order
violations surface as data — ``refused`` with the reason and the
admissible next verbs; a pending question travels as payload; a
non-canonical answer is an AskRefusal, passed through unchanged.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from deepagents.backends.filesystem import FilesystemBackend

from socrates.asking import AskRefusal
from socrates.refusal import Refusal


def invoke(
    verb: Callable[[Any, Any], dict[str, Any]],
    argv: list[str],
) -> dict[str, Any]:
    """Run one invocation file's verb — JSON in, payload out, never a trace."""
    try:
        root, data = _parse(argv)
        backend = FilesystemBackend(root_dir=root, virtual_mode=True)
        payload = verb(backend, data)
    except AskRefusal as exc:
        payload = exc.payload
    except Refusal as exc:
        payload = {
            "ok": False,
            "refused": True,
            "reason": exc.reason,
            "admissible_next": exc.admissible,
        }
    except (ValueError, KeyError) as exc:
        payload = {"ok": False, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 — the boundary is never a traceback
        payload = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return payload


def emit(main: Callable[[list[str]], dict[str, Any]]) -> None:
    """The only place an invocation meets stdout."""
    print(json.dumps(main(sys.argv[1:]), indent=2))


def _parse(argv: list[str]) -> tuple[Path, Any]:
    args = list(argv)
    root = Path.cwd()
    positional: list[str] = []
    while args:
        arg = args.pop(0)
        if arg == "--root":
            if not args:
                raise ValueError("--root requires the session directory")
            root = Path(args.pop(0))
        else:
            positional.append(arg)
    if len(positional) > 1:
        raise ValueError("expected one JSON argument (or none, to read stdin)")
    if positional:
        return root, json.loads(positional[0])
    return root, _stdin_json()


def _stdin_json() -> Any:
    try:
        text = sys.stdin.read()
    except OSError:
        return None
    if not text.strip():
        return None
    return json.loads(text)
