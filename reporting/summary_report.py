"""Generates a polished, stakeholder-friendly HTML execution summary.

This module is intentionally separate from pytest-html. It groups every
logged automation action ("test case") under the 5 business scenarios of
the IT Equipment Claim flow - Login & Logout, Claim Submission, Claim
Initiated, Claim Reviewed, and Claim Approved - instead of the underlying
pytest test-function names, so the report reads like a business workflow
rather than a technical test log. It never exposes raw stack traces, so
the report is suitable to share outside the QA team.
"""

import re
from datetime import datetime
from html import escape
from pathlib import Path


# The 5 business scenarios of the claim flow, in the order they should be
# rendered. "Login & Logout" is intentionally first and shared by every
# user, since each stage of the flow starts (and often ends) with a login.
SECTION_ORDER = [
    "Login & Logout",
    "Claim Submission",
    "Claim Initiated",
    "Claim Reviewed",
    "Claim Approved",
]

_LOGIN_USER_PATTERN = re.compile(r"Enter login email:\s*(\S+)", re.IGNORECASE)

_LOGIN_KEYWORDS = (
    "open the email login page",
    "enter login email",
    "click send otp",
    "enter the otp",
    "click verify otp",
    "log out",
    "logged out",
    "profile menu",
    "preparing logout",
)

_CLAIM_SUBMISSION_KEYWORDS = (
    "click add claim",
    "search for member",
    "select member:",
    "complete the claim form",
    "upload the invoice",
    "category value after selection",
    "duplicate invoice",
    "claim amount is non-zero",
    "checkbox",
    "open the claim preview",
    "submit the claim from the preview",
    "claim submitted;",
)

_APPROVAL_KEYWORDS = (
    "click review & approve",
    "save and continue approval",
    "confirm approval submission",
    "e-sign request sent",
    "wait for sanchalan setu e-sign",
    "claim approved successfully",
)


def _format_duration(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    minutes, secs = divmod(seconds, 60)
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def _scenario_status_badge(status: str) -> str:
    labels = {
        "passed": ("PASSED", "badge-passed"),
        "failed": ("FAILED", "badge-failed"),
        "not_executed": ("NOT EXECUTED", "badge-skipped"),
    }
    label, css_class = labels.get(status, (status.upper(), "badge-skipped"))
    return f'<span class="badge {css_class}">{label}</span>'


def _classify_step(text_lower: str, current_category: str) -> str:
    """Determines which of the 5 business scenarios a step belongs to.

    Uses the running/current category as a fallback so that steps without
    a distinctive keyword (e.g. "Add the claim note", "Forward the claim
    to the selected user") correctly inherit whichever scenario is active,
    based on the last explicit signal seen (a login action or a claim
    status transition).
    """
    if any(keyword in text_lower for keyword in _LOGIN_KEYWORDS):
        return "Login & Logout"
    if "status submitted" in text_lower:
        return "Claim Initiated"
    if "status initiated" in text_lower:
        return "Claim Reviewed"
    if "status reviewed" in text_lower:
        return "Claim Approved"
    if any(keyword in text_lower for keyword in _CLAIM_SUBMISSION_KEYWORDS):
        return "Claim Submission"
    if any(keyword in text_lower for keyword in _APPROVAL_KEYWORDS):
        return "Claim Approved"
    return current_category


def _build_sections(results):
    """Flattens all test-case steps (across every pytest test in this run)
    into the 5 business scenarios, tracking the active user as it goes.
    """
    sections = {name: [] for name in SECTION_ORDER}
    current_category = "Login & Logout"
    current_user = None

    for result in results:
        steps = result.get("steps") or []
        last_index = len(steps) - 1
        for index, step_text in enumerate(steps):
            text_lower = step_text.lower()

            user_match = _LOGIN_USER_PATTERN.search(step_text)
            if user_match:
                current_user = user_match.group(1)

            current_category = _classify_step(text_lower, current_category)

            is_last_step_of_test = index == last_index
            failed = result["outcome"] == "failed" and is_last_step_of_test

            sections[current_category].append(
                {
                    "text": step_text,
                    "user": current_user or "-",
                    "status": "Failed" if failed else "Passed",
                }
            )

    return sections


def _build_section_html(section_name: str, index: int, rows) -> str:
    total = len(rows)
    failed = sum(1 for row in rows if row["status"] == "Failed")
    passed = total - failed

    if total == 0:
        scenario_status = "not_executed"
        summary_text = "Not executed in this run"
    elif failed:
        scenario_status = "failed"
        summary_text = f"{passed}/{total} Passed"
    else:
        scenario_status = "passed"
        summary_text = f"{passed}/{total} Passed"

    if not rows:
        table_body = (
            '<tr><td colspan="4" class="empty-row">'
            "No test cases executed in this run.</td></tr>"
        )
    else:
        row_html = []
        for position, row in enumerate(rows, start=1):
            row_class = "row-failed" if row["status"] == "Failed" else "row-passed"
            icon = "&#10007;" if row["status"] == "Failed" else "&#10003;"
            row_html.append(
                f'<tr class="{row_class}">'
                f"<td>{position}</td>"
                f"<td>{escape(row['text'])}</td>"
                f"<td>{escape(row['user'])}</td>"
                f'<td class="status-cell"><span class="row-icon">{icon}</span>{row["status"]}</td>'
                f"</tr>"
            )
        table_body = "\n".join(row_html)

    return f"""
    <div class="scenario-section">
        <div class="scenario-header">
            <div class="scenario-title">{index}. {escape(section_name)}</div>
            <div class="scenario-header-right">
                <span class="scenario-count">{summary_text}</span>
                {_scenario_status_badge(scenario_status)}
            </div>
        </div>
        <table class="scenario-table">
            <thead>
                <tr>
                    <th class="col-num">#</th>
                    <th>Test Case</th>
                    <th class="col-user">User</th>
                    <th class="col-status">Status</th>
                </tr>
            </thead>
            <tbody>
                {table_body}
            </tbody>
        </table>
    </div>
    """


def generate_summary_report(
    results,
    total_duration_seconds: float,
    browser_name: str,
    headless: bool,
    output_path: Path,
) -> Path:
    sections = _build_sections(results)

    total_scenarios = len(SECTION_ORDER)
    executed_scenarios = sum(1 for name in SECTION_ORDER if sections[name])

    all_rows = [row for name in SECTION_ORDER for row in sections[name]]
    total_cases = len(all_rows)
    passed_cases = sum(1 for row in all_rows if row["status"] == "Passed")
    failed_cases = total_cases - passed_cases
    pass_rate = round((passed_cases / total_cases) * 100, 1) if total_cases else 0.0

    login_users = sorted(
        {user for r in results for user in (r.get("login_users") or [])}
    )
    login_users_display = ", ".join(login_users) if login_users else "N/A"

    browser_mode = "Headless" if headless else "Headed (visible browser)"
    generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p")

    scenario_sections_html = "".join(
        _build_section_html(name, position, sections[name])
        for position, name in enumerate(SECTION_ORDER, start=1)
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Automation Execution Summary</title>
<style>
    * {{ box-sizing: border-box; }}
    body {{
        margin: 0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: #f2f4f8;
        color: #1f2430;
    }}
    .header {{
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #a855f7 100%);
        color: #fff;
        padding: 36px 48px;
    }}
    .header h1 {{
        margin: 0 0 6px 0;
        font-size: 28px;
        letter-spacing: 0.5px;
    }}
    .header p {{
        margin: 0;
        opacity: 0.9;
        font-size: 14px;
    }}
    .container {{
        max-width: 1150px;
        margin: -28px auto 40px auto;
        padding: 0 24px;
    }}
    .summary-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 16px;
        margin-bottom: 28px;
    }}
    .summary-card {{
        background: #fff;
        border-radius: 12px;
        padding: 20px 16px;
        text-align: center;
        box-shadow: 0 6px 18px rgba(31, 36, 48, 0.08);
    }}
    .summary-card .value {{
        font-size: 30px;
        font-weight: 700;
        margin-bottom: 4px;
    }}
    .summary-card .label {{
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #6b7280;
    }}
    .value.scenarios {{ color: #4f46e5; }}
    .value.cases {{ color: #7c3aed; }}
    .value.passed {{ color: #16a34a; }}
    .value.failed {{ color: #dc2626; }}
    .value.rate {{ color: #0891b2; }}
    .info-bar {{
        background: #fff;
        border-radius: 12px;
        padding: 18px 24px;
        display: flex;
        flex-wrap: wrap;
        gap: 24px;
        margin-bottom: 28px;
        box-shadow: 0 6px 18px rgba(31, 36, 48, 0.08);
        font-size: 14px;
    }}
    .info-bar div {{ min-width: 180px; }}
    .info-bar strong {{ display: block; color: #6b7280; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
    .section-title {{
        font-size: 18px;
        font-weight: 600;
        margin: 8px 0 16px 4px;
        color: #1f2430;
    }}
    .scenario-section {{
        background: #fff;
        border-radius: 12px;
        padding: 20px 22px;
        margin-bottom: 20px;
        box-shadow: 0 6px 18px rgba(31, 36, 48, 0.08);
    }}
    .scenario-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        flex-wrap: wrap;
        gap: 10px;
    }}
    .scenario-title {{ font-size: 16.5px; font-weight: 700; color: #1f2430; }}
    .scenario-header-right {{ display: flex; align-items: center; gap: 12px; }}
    .scenario-count {{ font-size: 12.5px; color: #6b7280; font-weight: 600; }}
    .badge {{
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }}
    .badge-passed {{ background: #dcfce7; color: #16a34a; }}
    .badge-failed {{ background: #fee2e2; color: #dc2626; }}
    .badge-skipped {{ background: #f3f4f6; color: #6b7280; }}
    .scenario-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }}
    .scenario-table thead th {{
        text-align: left;
        color: #6b7280;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 8px 10px;
        border-bottom: 2px solid #f0f1f4;
    }}
    .scenario-table .col-num {{ width: 36px; }}
    .scenario-table .col-user {{ width: 220px; }}
    .scenario-table .col-status {{ width: 100px; }}
    .scenario-table tbody td {{
        padding: 8px 10px;
        border-bottom: 1px dashed #eef0f4;
        color: #374151;
        vertical-align: top;
    }}
    .scenario-table tbody tr:last-child td {{ border-bottom: none; }}
    .row-icon {{ display: inline-block; width: 16px; font-weight: 700; }}
    .row-passed .row-icon {{ color: #16a34a; }}
    .row-failed .row-icon {{ color: #dc2626; }}
    .row-passed .status-cell {{ color: #16a34a; font-weight: 700; font-size: 11.5px; text-transform: uppercase; }}
    .row-failed .status-cell {{ color: #dc2626; font-weight: 700; font-size: 11.5px; text-transform: uppercase; }}
    .row-failed td {{ background: #fef2f2; }}
    .empty-row {{ color: #9ca3af; font-style: italic; text-align: center; padding: 16px !important; }}
    .footer {{
        text-align: center;
        color: #9ca3af;
        font-size: 12px;
        margin-top: 30px;
        padding-bottom: 20px;
    }}
</style>
</head>
<body>
    <div class="header">
        <h1>IT Equipment Claim &mdash; Automation Execution Summary</h1>
        <p>Generated on {generated_at}</p>
    </div>
    <div class="container">
        <div class="summary-grid">
            <div class="summary-card"><div class="value scenarios">{executed_scenarios}/{total_scenarios}</div><div class="label">Test Scenarios Executed</div></div>
            <div class="summary-card"><div class="value cases">{total_cases}</div><div class="label">Total Test Cases</div></div>
            <div class="summary-card"><div class="value passed">{passed_cases}</div><div class="label">Passed</div></div>
            <div class="summary-card"><div class="value failed">{failed_cases}</div><div class="label">Failed</div></div>
            <div class="summary-card"><div class="value rate">{pass_rate}%</div><div class="label">Pass Rate</div></div>
        </div>
        <div class="info-bar">
            <div><strong>User Login(s)</strong>{escape(login_users_display)}</div>
            <div><strong>Browser Coverage</strong>{escape(browser_name)} ({escape(browser_mode)})</div>
            <div><strong>Total Execution Time</strong>{_format_duration(total_duration_seconds)}</div>
            <div><strong>Report Generated</strong>{generated_at}</div>
        </div>
        <div class="section-title">Test Scenarios &amp; Test Case Results</div>
        {scenario_sections_html}
        <div class="footer">Automation Execution Summary &bull; Playwright + pytest &bull; Page Object Model</div>
    </div>
</body>
</html>
"""

    output_path.write_text(html, encoding="utf-8")
    return output_path
