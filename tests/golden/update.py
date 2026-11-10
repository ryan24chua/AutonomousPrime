"""Rewrite the golden-master snapshot from the current code.

    python -m tests.golden.update

Only for a commit that is meant to change behaviour: state in that commit which numbers moved and why.
"""

import json

from tests.golden.capture import SNAPSHOT, capture


def main() -> None:
    data = capture()
    SNAPSHOT.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {SNAPSHOT} ({len(data['evaluation'])} evaluation rows, {len(data['console'])} console rows)")


if __name__ == "__main__":
    main()
