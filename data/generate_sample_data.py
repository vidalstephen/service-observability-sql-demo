#!/usr/bin/env python3
"""Generate deterministic synthetic service-observability data.

The data models a retail robotics service operation with clients, stores, robots,
scan runs, deliverables, issue tags, and labeling workload.
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data"
random.seed(42)

CLIENTS = [
    ("C001", "NorthMart", 0.965, 24),
    ("C002", "FreshBasket", 0.970, 18),
    ("C003", "ValueHub", 0.955, 30),
    ("C004", "UrbanGoods", 0.960, 20),
]
ISSUES = ["none", "labeling_backlog", "robot_offline", "camera_blur", "planogram_mismatch", "late_ingestion", "store_access_delay"]
FIRMWARES = ["4.8.1", "4.8.2", "4.9.0"]

def write_csv(name: str, rows: list[dict]) -> None:
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    start = date(2026, 5, 25)
    days = 42
    clients = []
    stores = []
    robots = []
    runs = []
    issues = []

    for client_id, client_name, accuracy_sla, timeliness_sla_hours in CLIENTS:
        clients.append({
            "client_id": client_id,
            "client_name": client_name,
            "accuracy_sla": accuracy_sla,
            "timeliness_sla_hours": timeliness_sla_hours,
            "contracted_weekly_scans": 42 + random.randint(-6, 8),
        })
        for s in range(1, 5):
            store_id = f"{client_id}-S{s:02d}"
            stores.append({"store_id": store_id, "client_id": client_id, "region": random.choice(["East", "Central", "West"])})
            for r in range(1, 3):
                robot_id = f"{store_id}-R{r}"
                firmware = random.choice(FIRMWARES)
                robots.append({"robot_id": robot_id, "store_id": store_id, "firmware_version": firmware})

    run_id = 1
    for offset in range(days):
        run_date = start + timedelta(days=offset)
        for robot in robots:
            if random.random() < 0.84:
                client_id = robot["store_id"].split("-")[0]
                client = next(c for c in clients if c["client_id"] == client_id)
                base_accuracy = client["accuracy_sla"] + random.uniform(-0.012, 0.018)
                issue = "none"

                # Inject realistic regressions in the final 14 days.
                if run_date >= start + timedelta(days=28):
                    if client_id == "C002" and robot["firmware_version"] == "4.9.0" and random.random() < 0.42:
                        base_accuracy -= random.uniform(0.020, 0.045)
                        issue = "camera_blur"
                    elif client_id == "C003" and random.random() < 0.28:
                        base_accuracy -= random.uniform(0.015, 0.035)
                        issue = "labeling_backlog"
                    elif random.random() < 0.09:
                        issue = random.choice(ISSUES[1:])
                elif random.random() < 0.07:
                    issue = random.choice(ISSUES[1:])
                    base_accuracy -= random.uniform(0.006, 0.020)

                labels_required = random.randint(850, 1500)
                if issue == "labeling_backlog":
                    labels_required += random.randint(450, 900)
                processing_hours = random.gauss(14, 3)
                if issue in {"labeling_backlog", "late_ingestion"}:
                    processing_hours += random.uniform(8, 18)
                if issue == "store_access_delay":
                    processing_hours += random.uniform(5, 12)
                processing_hours = max(4, processing_hours)
                accuracy = max(0.88, min(0.992, base_accuracy))
                delivered_on_time = int(processing_hours <= client["timeliness_sla_hours"])
                accuracy_met = int(accuracy >= client["accuracy_sla"])

                runs.append({
                    "run_id": run_id,
                    "run_date": run_date.isoformat(),
                    "client_id": client_id,
                    "store_id": robot["store_id"],
                    "robot_id": robot["robot_id"],
                    "firmware_version": robot["firmware_version"],
                    "labels_required": labels_required,
                    "processing_hours": round(processing_hours, 2),
                    "accuracy": round(accuracy, 4),
                    "accuracy_met": accuracy_met,
                    "delivered_on_time": delivered_on_time,
                    "issue_category": issue,
                })
                if issue != "none":
                    issues.append({
                        "issue_id": f"ISS-{run_id:05d}",
                        "run_id": run_id,
                        "opened_date": run_date.isoformat(),
                        "owner_team": random.choice(["Data Labeling", "Robot Ops", "Computer Vision", "Solutions Engineering"]),
                        "status": random.choice(["open", "investigating", "mitigated", "verified"]),
                        "issue_category": issue,
                    })
                run_id += 1

    write_csv("clients.csv", clients)
    write_csv("stores.csv", stores)
    write_csv("robots.csv", robots)
    write_csv("service_runs.csv", runs)
    write_csv("issues.csv", issues or [{"issue_id":"", "run_id":"", "opened_date":"", "owner_team":"", "status":"", "issue_category":""}])
    print(f"Generated {len(runs)} service runs and {len(issues)} issue records in {OUT}")

if __name__ == "__main__":
    main()
