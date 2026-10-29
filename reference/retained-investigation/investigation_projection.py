"""Loss-accounted model projections; complete captured bytes remain in the receipt."""

import json
from datetime import datetime


def instant(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone_required")
    return parsed


def project_logs(raw, start, end):
    begin, finish = instant(start), instant(end)
    if begin > finish:
        raise ValueError("observation_window")
    lines = raw.splitlines()
    counts = dict(
        captured=len(lines),
        included=0,
        before_window=0,
        after_window=0,
        undated_or_unparsed=0,
    )
    groups = {}
    volatile = {"request_id", "time", "started_at", "finished_at", "duration_ms"}
    for index, line in enumerate(lines, 1):
        try:
            row = json.loads(line)
            when = instant(row.get("time") or row.get("started_at"))
        except (ValueError, TypeError, AttributeError):
            counts["undated_or_unparsed"] += 1
            continue
        if when < begin:
            counts["before_window"] += 1
            continue
        if when > finish:
            counts["after_window"] += 1
            continue
        fields = {k: v for k, v in row.items() if k not in volatile}
        key = json.dumps(fields, sort_keys=True)
        if key not in groups:
            if len(groups) >= 12:
                raise ValueError("projection_group_limit")
            groups[key] = {
                "fields": fields,
                "count": 0,
                "source_rows": [],
                "first_at": when.isoformat(),
                "last_at": when.isoformat(),
            }
        group = groups[key]
        group["count"] += 1
        group["source_rows"].append(index)
        group["last_at"] = when.isoformat()
        counts["included"] += 1
    return {
        "window": {"start": start, "end": end},
        "counts": counts,
        "groups": list(groups.values()),
        "projection": "All captured dated records in the window, grouped by all fields except request_id, time, started_at, finished_at and duration_ms. No success/error filtering. One-based source rows identify originals. Capture is bounded, not complete cluster history.",
    }
