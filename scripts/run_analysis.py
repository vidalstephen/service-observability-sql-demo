#!/usr/bin/env python3
"""Build demo DB, run SQL analyses, and write portfolio-ready outputs."""
from __future__ import annotations

import csv
import html
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SQL = ROOT / "sql"
OUT = ROOT / "outputs"
DB = OUT / "service_observability.sqlite"

TABLES = {
    "clients": DATA / "clients.csv",
    "stores": DATA / "stores.csv",
    "robots": DATA / "robots.csv",
    "service_runs": DATA / "service_runs.csv",
    "issues": DATA / "issues.csv",
}


def load_csv(conn: sqlite3.Connection, table: str, path: Path) -> None:
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return
    cols = list(rows[0].keys())
    conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.execute(f"CREATE TABLE {table} ({', '.join(c + ' TEXT' for c in cols)})")
    conn.executemany(
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
        [[r[c] for c in cols] for r in rows],
    )


def normalize_types(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_runs_date ON service_runs(run_date);
        CREATE INDEX IF NOT EXISTS idx_runs_client ON service_runs(client_id);
        CREATE INDEX IF NOT EXISTS idx_runs_robot ON service_runs(robot_id);
        """
    )


def query_to_rows(conn: sqlite3.Connection, sql_path: Path) -> tuple[list[str], list[tuple]]:
    cur = conn.execute(sql_path.read_text())
    return [d[0] for d in cur.description], cur.fetchall()


def write_csv_output(name: str, headers: list[str], rows: list[tuple]) -> None:
    with (OUT / name).open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def md_table(headers: list[str], rows: list[tuple], limit: int = 12) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows[:limit]:
        out.append("| " + " | ".join(str(x) for x in row) + " |")
    if len(rows) > limit:
        out.append(f"| … | {len(rows) - limit} more rows |  |")
    return "\n".join(out)


def status_class(value: str) -> str:
    return {"red": "bad", "yellow": "warn", "green": "good", "investigate_now": "bad", "watchlist": "warn", "stable": "good"}.get(value, "")


def write_html(results: dict[str, tuple[list[str], list[tuple]]]) -> None:
    service_headers, service_rows = results["01_service_health"]
    regression_headers, regression_rows = results["02_regression_detection"]
    root_headers, root_rows = results["03_root_cause_patterns"]
    capacity_headers, capacity_rows = results["04_capacity_forecast"]

    def table(headers, rows, max_rows=20):
        body = []
        for row in rows[:max_rows]:
            cls = ""
            for cell in row:
                if str(cell) in {"red", "yellow", "green", "investigate_now", "watchlist", "stable"}:
                    cls = status_class(str(cell))
            body.append("<tr class='%s'>%s</tr>" % (cls, "".join(f"<td>{html.escape(str(c))}</td>" for c in row)))
        raw_table = "<table><thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (
            "".join(f"<th>{html.escape(h)}</th>" for h in headers), "\n".join(body)
        )
        return f'<div class="table-scroll" role="region" aria-label="Scrollable data table">{raw_table}</div>'

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Service Observability Dashboard</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: Inter, system-ui, -apple-system, Segoe UI, sans-serif; margin: 32px; color: #172033; background: #f6f8fb; }}
h1 {{ margin-bottom: 0; }}
.subtitle {{ color: #536076; margin-top: 6px; max-width: 960px; }}
.card {{ background: white; border: 1px solid #dfe5ef; border-radius: 14px; padding: 20px; margin: 18px 0; box-shadow: 0 8px 24px rgba(26,42,68,.06); max-width: 100%; overflow: hidden; }}
.card h2 {{ margin-top: 0; }}
.table-scroll {{ width: 100%; max-width: 100%; overflow-x: auto; overflow-y: hidden; -webkit-overflow-scrolling: touch; border: 1px solid #e9edf5; border-radius: 10px; }}
.table-scroll::after {{ content: 'Scroll table horizontally →'; display: none; color: #64748b; font-size: 12px; padding: 8px 10px; border-top: 1px solid #e9edf5; background: #f8fafc; }}
table {{ border-collapse: collapse; width: max-content; min-width: 100%; font-size: 13px; background: white; }}
th, td {{ border-bottom: 1px solid #e9edf5; padding: 8px 10px; text-align: left; vertical-align: top; white-space: nowrap; }}
th {{ color: #536076; font-weight: 700; background: #f8fafc; position: sticky; top: 0; z-index: 1; }}
td:last-child, th:last-child {{ white-space: normal; min-width: 150px; }}
tr:last-child td {{ border-bottom: 0; }}
tr.bad td:first-child::before {{ content: '● '; color: #dc2626; }}
tr.warn td:first-child::before {{ content: '● '; color: #d97706; }}
tr.good td:first-child::before {{ content: '● '; color: #16a34a; }}
.kpis {{ display:grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }}
.kpi {{ background: #0f172a; color:white; border-radius: 12px; padding: 16px; min-width: 0; }}
.kpi b {{ display:block; font-size: 24px; }}
.note {{ background:#fff7ed; border-left:4px solid #f97316; padding:12px 14px; max-width: 100%; }}
@media (max-width: 760px) {{
  body {{ margin: 14px; }}
  h1 {{ font-size: 26px; line-height: 1.1; }}
  .kpis {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
  .card {{ padding: 14px; border-radius: 12px; }}
  .table-scroll::after {{ display: block; }}
  table {{ font-size: 12px; }}
  th, td {{ padding: 7px 8px; }}
}}
@media (max-width: 420px) {{
  .kpis {{ grid-template-columns: 1fr; }}
}}
</style>
</head>
<body>
<h1>Service Observability Dashboard</h1>
<p class="subtitle">Synthetic retail robotics service data · SQL-generated scorecards · SLA, regression, root-cause, and capacity views</p>
<div class="kpis">
  <div class="kpi"><span>Clients monitored</span><b>{len(service_rows)}</b></div>
  <div class="kpi"><span>Regressions flagged</span><b>{sum(1 for r in regression_rows if str(r[-1]) == 'investigate_now')}</b></div>
  <div class="kpi"><span>Root-cause groups</span><b>{len(root_rows)}</b></div>
  <div class="kpi"><span>Capacity watch items</span><b>{sum(1 for r in capacity_rows if str(r[-1]) != 'capacity_ok')}</b></div>
</div>
<div class="card"><h2>Client service health</h2>{table(service_headers, service_rows)}</div>
<div class="card"><h2>Regression detection</h2>{table(regression_headers, regression_rows)}</div>
<div class="card"><h2>Root-cause patterns</h2>{table(root_headers, root_rows)}</div>
<div class="card"><h2>Capacity forecast</h2>{table(capacity_headers, capacity_rows)}</div>
<div class="note"><strong>Analyst note:</strong> This dashboard is generated from SQL queries in the repository. In a production BI tool, these queries would become modeled tables or dashboard tiles with owner, refresh cadence, and documented SLA definitions.</div>
</body>
</html>"""
    (OUT / "service_health_dashboard.html").write_text(html_doc)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    subprocess.run(["python3", str(DATA / "generate_sample_data.py")], check=True)
    if DB.exists():
        DB.unlink()
    conn = sqlite3.connect(DB)
    for table, path in TABLES.items():
        load_csv(conn, table, path)
    normalize_types(conn)
    conn.commit()

    results = {}
    for sql_path in sorted(SQL.glob("*.sql")):
        key = sql_path.stem
        headers, rows = query_to_rows(conn, sql_path)
        results[key] = (headers, rows)
        write_csv_output(key + ".csv", headers, rows)

    service = results["01_service_health"]
    regressions = [r for r in results["02_regression_detection"][1] if r[-1] == "investigate_now"]
    watch = [r for r in results["02_regression_detection"][1] if r[-1] == "watchlist"]

    report = [
        "# Generated Service Observability Report",
        "",
        "This report is generated by `scripts/run_analysis.py` from synthetic service data and SQL queries.",
        "",
        "## Executive summary",
        "",
        f"- Monitored **{len(service[1])} clients** across the most recent 14-day window.",
        f"- Flagged **{len(regressions)} investigate-now regressions** and **{len(watch)} watchlist regressions**.",
        "- Recommended follow-up is based on accuracy SLA attainment, timeliness SLA attainment, issue-rate deltas, and labeling capacity risk.",
        "",
        "## Client service health",
        "",
        md_table(*service),
        "",
        "## Regression detection",
        "",
        md_table(*results["02_regression_detection"]),
        "",
        "## Root-cause patterns",
        "",
        md_table(*results["03_root_cause_patterns"]),
        "",
        "## Capacity forecast",
        "",
        md_table(*results["04_capacity_forecast"]),
        "",
        "## Recommended analyst follow-up",
        "",
        "1. Review `investigate_now` rows with Computer Vision / Robot Ops owners.",
        "2. Open or update issue records for each repeated client + firmware + issue-category pattern.",
        "3. Confirm whether labeling backlog is capacity-driven, queue-health-driven, or data-quality-driven.",
        "4. Re-run this report after mitigations ship and verify the metric actually improved.",
    ]
    (OUT / "generated_report.md").write_text("\n".join(report))
    write_html(results)
    print(f"Wrote {DB}")
    print(f"Wrote {OUT / 'generated_report.md'}")
    print(f"Wrote {OUT / 'service_health_dashboard.html'}")

if __name__ == "__main__":
    main()
