#!/usr/bin/env python3
"""Build CHANGELOG.md from observations/*.jsonl: one line per field that changed between consecutive re-tests.
Lists (e.g. free model names) are reported as added/removed items. Newest first."""
import json, pathlib
root = pathlib.Path(__file__).resolve().parent.parent
SKIP = {"at", "ok", "note"}
rows = []
for f in sorted((root / "observations").glob("*.jsonl")):
    src = f.stem
    obs = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    obs = [o for o in obs if o.get("ok")]
    for prev, cur in zip(obs, obs[1:]):
        changes = []
        for k in sorted(set(prev) | set(cur)):
            if k in SKIP or prev.get(k) == cur.get(k):
                continue
            a, b = prev.get(k), cur.get(k)
            if isinstance(a, list) and isinstance(b, list) and all(isinstance(x, dict) and "title" in x for x in a + b):
                A = {x["title"]: x for x in a}; B = {x["title"]: x for x in b}
                parts = [f'new: "{t}"' for t in B if t not in A] + [f'gone: "{t}"' for t in A if t not in B]
                for t in A.keys() & B.keys():
                    d = [f"{f} {A[t].get(f)} → {B[t].get(f)}" for f in sorted(set(A[t]) | set(B[t])) if f != "title" and A[t].get(f) != B[t].get(f)]
                    if d: parts.append(f'"{t}": ' + ", ".join(d))
                changes.append(f"{k}: {'; '.join(parts)}")
            elif isinstance(a, list) and isinstance(b, list):
                add = [x for x in b if x not in a]; rem = [x for x in a if x not in b]
                parts = ([f"+{', +'.join(map(str, add))}"] if add else []) + ([f"-{', -'.join(map(str, rem))}"] if rem else [])
                changes.append(f"{k}: {'; '.join(parts)}")
            else:
                changes.append(f"{k}: {a} → {b}")
        if changes:
            rows.append((cur["at"], src, changes))
rows.sort(key=lambda r: r[0], reverse=True)
out = ["# Changelog", "", "Generated from `observations/` by `scripts/changelog.py` after each re-test. "
       "Only changes are listed; a source with no line for a day was unchanged.", ""]
day = None
for at, src, changes in rows:
    if at[:10] != day:
        day = at[:10]; out += ["", f"## {day}"]
    out.append(f"- **{src}**: " + " · ".join(changes))
(root / "CHANGELOG.md").write_text("\n".join(out).replace("\n\n\n", "\n\n") + "\n")
print(f"{len(rows)} change rows")
