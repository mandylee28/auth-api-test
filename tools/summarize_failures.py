"""Summarize pytest failures from a JUnit XML report.

Usage:
    pytest --junitxml=report.xml
    python tools/summarize_failures.py report.xml
"""

import sys
import xml.etree.ElementTree as ET


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python tools/summarize_failures.py <junit-xml>")
        return 2

    tree = ET.parse(sys.argv[1])
    root = tree.getroot()

    suites = root.findall("testsuite") or [root]
    total = failed = 0
    failures = []

    for suite in suites:
        total += int(suite.get("tests", 0))
        failed += int(suite.get("failures", 0)) + int(suite.get("errors", 0))
        for case in suite.findall("testcase"):
            failure = case.find("failure")
            if failure is None:
                failure = case.find("error")
            if failure is None:
                continue
            name = f"{case.get('classname', '')}::{case.get('name', '')}"
            message = (failure.get("message") or "").strip().splitlines()
            detail = [line for line in (failure.text or "").strip().splitlines() if line.strip()]
            failures.append((name, message[0] if message else "", detail[-1] if detail else ""))

    print(f"Total: {total}  Passed: {total - failed}  Failed: {failed}")
    if not failures:
        print("All passed.")
        return 0

    print()
    for name, message, last_line in failures:
        print(f"FAILED: {name}")
        if message:
            print(f"  {message}")
        if last_line and last_line != message:
            print(f"  {last_line}")
        print()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
