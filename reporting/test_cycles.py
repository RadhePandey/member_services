"""Test cycle register: one folder per cycle under reports/test_cycles with its
reports, logs and bug evidence, plus cycles.json and an index.html listing
every cycle with date/time, build version, changes, scope and results.

    from reporting.test_cycles import start_cycle, add_artifact, finish_cycle
    cycle = start_cycle("Member Onboarding (MPA)", build="1.4.2", changes="...", scope="...")
    add_artifact(cycle["id"], "Bug report", "path/to/bug_report.html", kind="report")
    finish_cycle(cycle["id"], summary={"Passed": 10, "Failed": 2, "Bugs": 3})

When no build version is given, cycles use DEFAULT_BUILD; call
set_build(cycle_id, "1.4.2", changes="...") once the real build is known.

Run `python -m reporting.test_cycles` to rebuild index.html.
"""
import html
import json
import shutil
from datetime import datetime
from pathlib import Path

CYCLES_DIR = Path(__file__).resolve().parents[1] / "reports" / "test_cycles"
REGISTER = CYCLES_DIR / "cycles.json"
NOT_PROVIDED = "Not provided"
DEFAULT_BUILD = "Build 1.0 (default)"


def _load():
    if REGISTER.exists():
        return json.loads(REGISTER.read_text("utf-8"))
    return []


def _save(cycles):
    CYCLES_DIR.mkdir(parents=True, exist_ok=True)
    REGISTER.write_text(json.dumps(cycles, indent=2, ensure_ascii=False), "utf-8")
    render_index(cycles)


def _get(cycles, cycle_id):
    for cycle in cycles:
        if cycle["id"] == cycle_id:
            return cycle
    raise KeyError(f"Unknown test cycle {cycle_id}")


def start_cycle(module, build=DEFAULT_BUILD, changes=NOT_PROVIDED, scope="",
                environment="https://test.rajyasabha.digital (stage)", tester="", started=None):
    """Register a new cycle and create its folder; returns the cycle record."""
    cycles = _load()
    started = started or datetime.now()
    cycle_id = f"Cycle-{len(cycles) + 1:02d}"
    folder = f"{cycle_id}_{started:%Y-%m-%d_%H%M}"
    (CYCLES_DIR / folder).mkdir(parents=True, exist_ok=True)
    cycle = {
        "id": cycle_id, "folder": folder, "module": module, "build": build or DEFAULT_BUILD,
        "changes": changes or NOT_PROVIDED, "scope": scope, "environment": environment,
        "tester": tester, "started": started.strftime("%Y-%m-%d %H:%M"), "ended": "",
        "status": "In progress", "summary": {}, "artifacts": [],
    }
    cycles.append(cycle)
    _save(cycles)
    return cycle


def cycle_dir(cycle_id):
    return CYCLES_DIR / _get(_load(), cycle_id)["folder"]


def add_artifact(cycle_id, title, source, kind="report", time=None, copy=True):
    """Copy a report/log (file or folder) into the cycle folder and list it."""
    cycles = _load()
    cycle = _get(cycles, cycle_id)
    source = Path(source)
    target = CYCLES_DIR / cycle["folder"] / kind / source.name
    if copy:
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            shutil.copy2(source, target)
    path = target.relative_to(CYCLES_DIR).as_posix()
    cycle["artifacts"] = [a for a in cycle["artifacts"] if a["path"] != path]  # re-runs replace, not duplicate
    cycle["artifacts"].append({
        "title": title, "kind": kind,
        "path": path,
        "time": time or datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    _save(cycles)
    return target


def set_build(cycle_id, build, changes=None):
    """Record the real build version (and change list) of a cycle."""
    cycles = _load()
    cycle = _get(cycles, cycle_id)
    cycle["build"] = build
    if changes:
        cycle["changes"] = changes
    _save(cycles)


def finish_cycle(cycle_id, summary=None, status="Completed", ended=None):
    cycles = _load()
    cycle = _get(cycles, cycle_id)
    cycle["summary"].update(summary or {})
    cycle["status"] = status
    cycle["ended"] = (ended or datetime.now()).strftime("%Y-%m-%d %H:%M")
    _save(cycles)


def render_index(cycles=None):
    cycles = _load() if cycles is None else cycles
    e = html.escape
    rows = []
    for c in reversed(cycles):
        summary = " · ".join(f"{e(k)}: <b>{e(str(v))}</b>" for k, v in c["summary"].items())
        artifacts = "".join(
            f"<li><a href='{e(a['path'])}' target='_blank'>{e(a['title'])}</a>"
            f" <span class=muted>{e(a['kind'])} · {e(a['time'])}</span></li>" for a in c["artifacts"])
        rows.append(f"""<article>
<div class="head"><h2>{e(c['id'])} — {e(c['module'])}</h2><span class="status">{e(c['status'])}</span></div>
<dl>
<dt>Date / time</dt><dd>{e(c['started'])}{(' → ' + e(c['ended'])) if c['ended'] else ''}</dd>
<dt>Build version</dt><dd>{e(c['build'])}</dd>
<dt>Changes in build</dt><dd>{e(c['changes'])}</dd>
<dt>Scope</dt><dd>{e(c['scope'])}</dd>
<dt>Environment</dt><dd>{e(c['environment'])}</dd>
{f"<dt>Tester</dt><dd>{e(c['tester'])}</dd>" if c['tester'] else ''}
<dt>Result</dt><dd>{summary or '—'}</dd>
</dl>
<h3>Reports, logs and evidence</h3><ul>{artifacts or '<li class=muted>None yet</li>'}</ul>
</article>""")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Test Cycles</title>
<style>
body {{ margin:0; font:15px/1.5 "Segoe UI",system-ui,sans-serif; background:#f4f6fb; color:#1d2433; }}
header {{ background:#1e3a8a; color:#fff; padding:22px 32px; }} header h1 {{ margin:0; font-size:22px; }}
main {{ max-width:1100px; margin:0 auto; padding:24px 16px 48px; }}
article {{ background:#fff; border:1px solid #e4e7ec; border-radius:10px; padding:18px 22px; margin-bottom:18px; }}
.head {{ display:flex; justify-content:space-between; align-items:center; gap:10px; }}
h2 {{ margin:0; font-size:18px; }} h3 {{ font-size:14px; margin:14px 0 4px; color:#475467; }}
.status {{ background:#dcfae6; color:#067647; border-radius:20px; padding:2px 12px; font-size:12px; font-weight:600; }}
dl {{ display:grid; grid-template-columns:max-content 1fr; gap:4px 18px; margin:12px 0 0; }}
dt {{ color:#667085; }} dd {{ margin:0; }} .muted {{ color:#667085; font-size:12px; }}
ul {{ margin:4px 0; padding-left:20px; }} a {{ color:#3538cd; }}
</style></head><body><header><h1>Test Cycles</h1></header><main>
{''.join(rows) or '<p>No test cycles yet.</p>'}</main></body></html>"""
    CYCLES_DIR.mkdir(parents=True, exist_ok=True)
    (CYCLES_DIR / "index.html").write_text(page, "utf-8")


if __name__ == "__main__":
    render_index()
    print(CYCLES_DIR / "index.html")
