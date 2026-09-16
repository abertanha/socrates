"""Ticket 03 (socrates-seam) — the gate knows who it imported.

The bootstrap gate verified importability, not identity: any package
named ``socrates`` on the import path passed, and a stale or foreign
engine would enforce a divergent method in Socrates' name, silently.
Now the package carries an identity marker, and the taught check asserts
three things after the import succeeds: the marker exists, the imported
package's own location resolves inside the repository derived from the
skill file's RESOLVED real location (through symlinks — the skill has
already circulated to machines it was not written on), and the marker
matches the repository's declared version — the only clause that catches
a stale engine sitting at the right path. A wrong-engine import is a
DISTINCT failure from a missing engine: another Socrates answered, and
installation steps are for the absent. No absolute path to any machine's
tree remains in the skill text.

Seam: the package marker, the skill artifact, and the taught derivation
executed as a subprocess (the recipe must discriminate, not merely read
well) — prior art: the v3 skin pin file.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / ".claude" / "skills" / "socrates" / "SKILL.md"


def _skill() -> str:
    return SKILL.read_text()


def _flat() -> str:
    return " ".join(_skill().split())


def _head_flat() -> str:
    text = _skill()
    return " ".join(text[: text.index("### The deliverable audit")].split())


# --- The marker -----------------------------------------------------------------


def test_the_package_exposes_a_stable_identity_marker():
    import socrates

    marker = getattr(socrates, "__version__", None)
    assert isinstance(marker, str) and marker, (
        "the package carries no identity marker"
    )
    declared = tomllib.loads((REPO / "pyproject.toml").read_text())
    assert marker == declared["project"]["version"], (
        "the marker drifted from the declared version"
    )


# --- The taught derivation runs, and it discriminates ------------------------------

# The gate's taught check, as code: resolve the skill file's real location,
# its directory is three directories below the root, import, then the three
# identity clauses.
_RECIPE = r"""
import os, re, sys
root = os.path.dirname(os.path.realpath(sys.argv[1]))
for _ in range(3):
    root = os.path.dirname(root)
import socrates
marker = getattr(socrates, "__version__", None)
origin = os.path.realpath(socrates.__file__)
ok = False
if marker and origin.startswith(root + os.sep):
    declared = open(os.path.join(root, "pyproject.toml")).read()
    found = re.search(r'version = "([^"]+)"', declared)
    ok = bool(found) and found.group(1) == marker
print("IDENTITY-OK" if ok else "IDENTITY-REFUSED")
"""


def _run_recipe(skill_path: Path, pythonpath: str) -> str:
    proc = subprocess.run(
        [sys.executable, "-c", _RECIPE, str(skill_path)],
        env={**os.environ, "PYTHONPATH": pythonpath},
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def test_the_taught_check_accepts_this_repository():
    out = _run_recipe(SKILL, str(REPO / "src"))
    assert "IDENTITY-OK" in out, out


def test_the_taught_derivation_survives_a_symlinked_skill_file(tmp_path):
    link = tmp_path / "SKILL.md"
    link.symlink_to(SKILL)
    out = _run_recipe(link, str(REPO / "src"))
    assert "IDENTITY-OK" in out, (
        "the three-up arithmetic broke on a symlinked skill file"
    )


def test_the_taught_check_refuses_a_decoy_package_ahead_on_the_path(tmp_path):
    """A foreign ``socrates`` with a marker of its own: the marker clause
    alone would pass it — the location clause is what refuses it."""
    decoy = tmp_path / "socrates"
    decoy.mkdir()
    (decoy / "__init__.py").write_text("__version__ = '9.9.9-foreign'\n")
    out = _run_recipe(
        SKILL, f"{tmp_path}{os.pathsep}{REPO / 'src'}"
    )
    assert "IDENTITY-REFUSED" in out, "a foreign Socrates answered"


def test_the_taught_check_refuses_a_stale_engine_at_the_right_path(tmp_path):
    """Right location, old code: the location clause passes it — the
    declared-version comparison is what refuses it."""
    root = tmp_path / "stale-repo"
    (root / "src" / "socrates").mkdir(parents=True)
    (root / "src" / "socrates" / "__init__.py").write_text(
        "__version__ = '0.0.9'\n"
    )
    (root / "pyproject.toml").write_text(
        '[project]\nname = "socrates"\nversion = "0.0.9"\n'
    )
    (root / ".claude" / "skills" / "socrates").mkdir(parents=True)
    skill = root / ".claude" / "skills" / "socrates" / "SKILL.md"
    skill.write_text("stale clone\n")

    in_place = _run_recipe(skill, str(root / "src"))
    assert "IDENTITY-OK" in in_place, "the clauses refused a matching clone"

    # The clone's pyproject moves on (a release cut); the imported engine
    # stays old — right path, wrong code.
    (root / "pyproject.toml").write_text(
        '[project]\nname = "socrates"\nversion = "0.1.0"\n'
    )
    stale = _run_recipe(skill, str(root / "src"))
    assert "IDENTITY-REFUSED" in stale, "a stale Socrates answered"


# --- The skin teaches it ------------------------------------------------------------


def test_the_gate_teaches_identity_not_mere_importability():
    flat = _head_flat()
    assert "identity marker" in flat, "the marker is untaught"
    assert "__version__" in flat, "the marker's name is untaught"
    assert "resolves inside" in flat, "the location clause is untaught"
    assert "pyproject.toml" in flat, "the declared-version source is untaught"
    assert "another Socrates answered" in flat, (
        "the wrong-engine wording is untaught"
    )


def test_wrong_engine_and_missing_engine_are_distinct_failures():
    flat = _head_flat()
    assert "no engine, no Socrates" in flat, "the missing-engine refusal moved"
    assert "only when the import fails" in flat, (
        "the steps would print for the wrong engine too"
    )
    assert "not the one this skill ships with" in flat, (
        "identity is not stated as identity"
    )
    assert "no installation step fixes identity" in flat, (
        "the steps would be offered as the cure"
    )


def test_the_derivation_is_taught_against_the_resolved_location():
    flat = _head_flat()
    assert "real location" in flat, "the resolution duty is missing"
    assert "through any symlinks" in flat, "the symlink case is untaught"
    assert "three directories up from the resolved location" in flat, (
        "the arithmetic runs against the unresolved path"
    )


def test_no_absolute_path_to_any_machine_remains():
    flat = _flat()
    assert "/home/" not in flat, "a machine's home tree is named"
    assert "/Users/" not in flat, "a machine's home tree is named"
    assert "the root the bootstrap gate derives" in flat, (
        "the glossary path is not derived from the gate's root"
    )


def test_the_runtime_agnostic_pin_still_holds_over_the_new_text():
    flat = _flat().casefold()
    for named in ("python", "bash", "shell", "pip ", "uvx", "terminal"):
        assert named not in flat, f"a runtime mechanism is named: {named!r}"


@pytest.mark.parametrize(
    "clause",
    [
        "identity marker",
        "another Socrates answered",
        "three directories up from the resolved location",
        "the root the bootstrap gate derives",
    ],
)
def test_every_identity_clause_sits_in_the_gate_section(clause):
    head = _head_flat()
    assert clause in head, f"the clause drifted out of the head: {clause!r}"
