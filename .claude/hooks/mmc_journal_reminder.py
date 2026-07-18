#!/usr/bin/env python3
"""Stop hook: once per session, remind the agent to consider writing an
MMC journal entry (D:\\Dev\\MMC\\journal\\<date>.md) before ending the turn.

Fires at most once per session_id via a marker file, so it can't loop
forever on repeated Stop events. This never writes the journal itself --
it only injects a reminder; a human or agent still has to judge relevance
and author the entry. See D:\\Dev\\MMC\\MMC.md.
"""
import json
import os
import sys
import tempfile

REASON = (
    "Reminder (artwebsite Stop hook, fires once per session): before finishing, "
    "check whether this session touched cross-system facts (Meta pixel/CAPI, ad "
    "campaigns, SEO loop, or anything relevant to the other three systems) or "
    "otherwise did meaningful, non-trivial work worth recording. If so, write a "
    "one-paragraph dated entry to D:\\Dev\\MMC\\journal\\<date>.md before stopping, "
    "per the convention in D:\\Dev\\MMC\\MMC.md (read that file first if you have "
    "not already this session). This is a reminder only -- use your own judgment "
    "on relevance and wording; do not mechanically generate the entry from a "
    "diff. If nothing this session rises to that bar, disregard this and finish "
    "normally."
)


def main():
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, ValueError):
        payload = {}

    session_id = payload.get("session_id") or "unknown"

    marker_dir = os.path.join(tempfile.gettempdir(), "claude-mmc-journal-reminder")
    os.makedirs(marker_dir, exist_ok=True)
    marker = os.path.join(marker_dir, session_id)

    if os.path.exists(marker):
        return

    open(marker, "w").close()
    print(json.dumps({"decision": "block", "reason": REASON}))


if __name__ == "__main__":
    main()
