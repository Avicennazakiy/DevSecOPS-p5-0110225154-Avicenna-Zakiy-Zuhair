"""Quality Gate SAST.

Membaca laporan JSON dari Bandit dan menggagalkan pipeline (exit code 1)
jika jumlah temuan melebihi ambang batas.

Ambang batas default: HIGH = 0, MEDIUM = 0 (LOW diizinkan).
Dapat diubah lewat environment variable MAX_HIGH dan MAX_MEDIUM.

Pemakaian: python scripts/quality_gate.py bandit-report.json
"""
import json
import os
import sys
from collections import Counter

SEVERITIES = ("HIGH", "MEDIUM", "LOW")


def load_thresholds():
    return {
        "HIGH": int(os.environ.get("MAX_HIGH", "0")),
        "MEDIUM": int(os.environ.get("MAX_MEDIUM", "0")),
    }


def evaluate(report, thresholds):
    """Kembalikan (counts, findings, daftar_pelanggaran)."""
    findings = report.get("results", [])
    counts = Counter(item["issue_severity"] for item in findings)
    violations = [
        f"{sev}: {counts[sev]} temuan (batas {limit})"
        for sev, limit in thresholds.items()
        if counts[sev] > limit
    ]
    return counts, findings, violations


def write_summary(counts, thresholds, violations):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    status = "GAGAL" if violations else "LULUS"
    lines = [
        f"## SAST Quality Gate: {status}",
        "",
        "| Severity | Temuan | Batas |",
        "|---|---|---|",
    ]
    for sev in SEVERITIES:
        limit = thresholds.get(sev, "-")
        lines.append(f"| {sev} | {counts[sev]} | {limit} |")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main(argv):
    if len(argv) != 2:
        print("Pemakaian: python scripts/quality_gate.py <bandit-report.json>")
        return 2

    with open(argv[1], encoding="utf-8") as handle:
        report = json.load(handle)

    thresholds = load_thresholds()
    counts, findings, violations = evaluate(report, thresholds)

    print("=== SAST Quality Gate ===")
    for sev in SEVERITIES:
        limit = thresholds.get(sev, "-")
        print(f"{sev:<7} temuan: {counts[sev]:<3} batas: {limit}")

    flagged = [f for f in findings if f["issue_severity"] in thresholds]
    for item in flagged:
        print(
            f"- [{item['issue_severity']}] {item['test_id']} "
            f"{item['filename']}:{item['line_number']} - {item['issue_text']}"
        )

    write_summary(counts, thresholds, violations)

    if violations:
        print("\nQUALITY GATE GAGAL:")
        for message in violations:
            print(f"  * {message}")
        return 1

    print("\nQUALITY GATE LULUS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
