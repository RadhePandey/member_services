import base64
from datetime import datetime
import io
import json
import os
from pathlib import Path
import re
import sys
import time

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from config import BROWSER_HEADLESS, BROWSER_KEEP_OPEN, BROWSER_SLOW_MO
from reporting.summary_report import generate_summary_report


SCREENSHOTS_DIR = Path(__file__).resolve().parent / "screenshots"
REPORTS_DIR = Path(__file__).resolve().parent / "reports"

_LOGIN_STEP_PATTERN = re.compile(r"Enter login email:\s*(\S+)")
_SESSION_RESULTS = []
_SESSION_START_TIME = None
_CAPTURED_STEP_OUTPUT = {}

# When multiple pytest invocations belong to the same logical end-to-end run
# (e.g. run_claim_e2e.bat calling pytest twice: forwarding stage, then
# approval stage), set E2E_RUN_ID to the same value for every invocation and
# set E2E_FINAL_STAGE=1 only on the last one. This accumulates each stage's
# results on disk and produces a single consolidated HTML report at the end
# instead of one report per pytest invocation.
_E2E_RUN_ID = os.environ.get("E2E_RUN_ID")
_E2E_FINAL_STAGE = os.environ.get("E2E_FINAL_STAGE") == "1"


class _StdoutTee:
    """Mirrors writes to the real stdout while also buffering them.

    This lets the reporting layer read [STEP] log lines for the executive
    summary even when tests run with `-s` (output capture disabled), without
    changing how or what the existing pages/tests print.
    """

    def __init__(self, original):
        self._original = original
        self.buffer = io.StringIO()

    def write(self, data):
        self._original.write(data)
        self.buffer.write(data)
        return len(data)

    def flush(self):
        self._original.flush()

    def __getattr__(self, name):
        return getattr(self._original, name)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    original_stdout = sys.stdout
    tee = _StdoutTee(original_stdout)
    sys.stdout = tee
    try:
        yield
    finally:
        sys.stdout = original_stdout
        _CAPTURED_STEP_OUTPUT[item.nodeid] = tee.buffer.getvalue()


def _safe_test_name(nodeid: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", nodeid).strip("_")


def pytest_configure(config):
    metadata = getattr(config, "_metadata", None)
    if metadata is not None:
        metadata.update(
            {
                "Automation": "Playwright + pytest",
                "Browser": "Chromium",
                "Headless": str(BROWSER_HEADLESS),
                "Python": "Python runtime used by pytest",
            }
        )


def pytest_sessionstart(session):
    global _SESSION_START_TIME
    _SESSION_START_TIME = time.time()
    _SESSION_RESULTS.clear()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        captured_text = _CAPTURED_STEP_OUTPUT.get(item.nodeid) or report.capstdout
        steps = re.findall(r"^\[STEP\]\s*(.+)$", captured_text, re.MULTILINE)
        login_users = list(dict.fromkeys(_LOGIN_STEP_PATTERN.findall(captured_text)))
        _SESSION_RESULTS.append(
            {
                "name": item.name,
                "nodeid": item.nodeid,
                "outcome": report.outcome,
                "duration": report.duration,
                "steps": steps,
                "login_users": login_users,
                "markers": [marker.name for marker in item.iter_markers()],
            }
        )
    elif report.when == "setup" and report.outcome != "passed":
        _SESSION_RESULTS.append(
            {
                "name": item.name,
                "nodeid": item.nodeid,
                "outcome": report.outcome,
                "duration": report.duration,
                "steps": [],
                "login_users": [],
                "markers": [marker.name for marker in item.iter_markers()],
            }
        )

    if report.when not in ("setup", "call") or not report.failed:
        return

    page = item.funcargs.get("page")
    if page is None:
        return

    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = SCREENSHOTS_DIR / (
        f"{_safe_test_name(item.nodeid)}_{report.when}_{timestamp}.png"
    )

    try:
        page.screenshot(path=str(screenshot_path), full_page=True)
    except PlaywrightError as error:
        print(
            f"[WARNING] Could not capture failure screenshot for "
            f"{item.nodeid}: {error}",
            flush=True,
        )
        return

    html_plugin = item.config.pluginmanager.getplugin("html")
    if html_plugin is not None:
        extras = getattr(report, "extras", [])
        image_data = base64.b64encode(screenshot_path.read_bytes()).decode("ascii")
        extras.append(
            html_plugin.extras.image(image_data, mime_type="image/png")
        )
        report.extras = extras


def pytest_sessionfinish(session, exitstatus):
    if not _SESSION_RESULTS:
        return

    stage_duration = time.time() - (_SESSION_START_TIME or time.time())
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if _E2E_RUN_ID:
        # Multi-stage run (e.g. run_claim_e2e.bat): accumulate this stage's
        # results and only render the HTML once the final stage finishes,
        # so the user gets ONE consolidated report for the whole flow.
        accumulator_path = REPORTS_DIR / f".e2e_run_{_E2E_RUN_ID}.json"
        stages = []
        if accumulator_path.exists():
            stages = json.loads(accumulator_path.read_text(encoding="utf-8"))
        stages.append({"results": _SESSION_RESULTS, "duration": stage_duration})

        if not _E2E_FINAL_STAGE:
            accumulator_path.write_text(json.dumps(stages), encoding="utf-8")
            print(
                "\nStage results captured for consolidated end-to-end report "
                "(will be generated after the final stage)."
            )
            return

        combined_results = []
        combined_duration = 0.0
        for stage in stages:
            combined_results.extend(stage["results"])
            combined_duration += stage["duration"]

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_path = REPORTS_DIR / f"execution_summary_{timestamp}.html"
        generate_summary_report(
            results=combined_results,
            total_duration_seconds=combined_duration,
            browser_name="Chromium",
            headless=BROWSER_HEADLESS,
            output_path=report_path,
        )
        accumulator_path.unlink(missing_ok=True)
        print(f"\nExecutive summary report: file:///{report_path.as_posix()}")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = REPORTS_DIR / f"execution_summary_{timestamp}.html"

    generate_summary_report(
        results=_SESSION_RESULTS,
        total_duration_seconds=stage_duration,
        browser_name="Chromium",
        headless=BROWSER_HEADLESS,
        output_path=report_path,
    )
    print(f"\nExecutive summary report: file:///{report_path.as_posix()}")


@pytest.fixture(scope="function")
def page():
    with sync_playwright() as playwright:
        launch_options = {
            "headless": BROWSER_HEADLESS,
            "slow_mo": BROWSER_SLOW_MO,
        }
        if not BROWSER_HEADLESS:
            launch_options["args"] = ["--start-maximized"]

        browser = playwright.chromium.launch(**launch_options)
        context_options = {"ignore_https_errors": True}
        if not BROWSER_HEADLESS:
            context_options["no_viewport"] = True
        else:
            context_options["viewport"] = {"width": 1920, "height": 900}

        context = browser.new_context(**context_options)
        page = context.new_page()
        yield page
        if BROWSER_KEEP_OPEN:
            page.pause()
        page.close()
        context.close()
        browser.close()
