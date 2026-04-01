from __future__ import annotations

import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def iter_py_files() -> list[Path]:
    files = []
    for p in ROOT.rglob("*.py"):
        if ".venv" in p.parts or "venv" in p.parts or "__pycache__" in p.parts:
            continue
        files.append(p)
    return sorted(files)


def main() -> int:
    print("Python executable:", sys.executable)
    py_files = iter_py_files()
    print("Found", len(py_files), "Python files")

    failures: list[tuple[Path, str]] = []
    for f in py_files:
        try:
            py_compile.compile(str(f), doraise=True)
            print("OK", f.relative_to(ROOT))
        except Exception as exc:
            failures.append((f, str(exc)))
            print("FAIL", f.relative_to(ROOT), "->", exc)

    if failures:
        print("\nValidation failed for", len(failures), "file(s)")
        return 1

    print("\nAll Python files compiled successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
