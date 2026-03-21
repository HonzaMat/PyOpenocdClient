#!/usr/bin/env python3

# SPDX-License-Identifier: MIT

import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from dataclasses import dataclass


DIRS_TO_INCLUDE = [
    "src/",
    "tests_unit/",
]


@dataclass
class CoverageEntry:
    filename: str
    coverage_rate: float


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Check that all code lines are fully covered"
    )

    def _check_existing_file(arg: str):
        f = Path(arg)
        if not f.is_file():
            raise argparse.ArgumentTypeError(f"This is not a file: {arg}")
        return f

    parser.add_argument(
        "coverage_xml",
        type=_check_existing_file,
        help="Path to the coverage report (*.xml) to check",
    )
    return parser.parse_args()


def get_coverage_entries(coverage_xml: Path) -> list[CoverageEntry]:

    result = []
    root = ET.fromstring(coverage_xml.read_text())
    for class_item in root.iter('class'):

        # safety
        if "filename" not in class_item.attrib:
            continue
        if "line-rate" not in class_item.attrib:
            continue

        filename = class_item.attrib["filename"]
        coverage_rate = float(class_item.attrib["line-rate"])

        if not any(filename.startswith(d) for d in DIRS_TO_INCLUDE):
            continue

        result += [CoverageEntry(filename=filename, coverage_rate=coverage_rate)]

    return result


def check_full_coverage(coverage_xml: Path) -> int:

    entries = get_coverage_entries(coverage_xml)

    if len(entries) == 0:
        print(f"No coverage entries were found in file {coverage_xml}!")
        return 1

    not_fully_covered = [e for e in entries if e.coverage_rate < 1]

    if len(not_fully_covered) > 0:
        print("Error: Full coverage not achieved.")
        print()
        print("These files contain uncovered lines:")
        for e in not_fully_covered:
            print(f"  {e.filename}")
        return 2

    print("Success: All files are fully covered.")
    return 0


def main() -> int:
    args = parse_args()
    return check_full_coverage(args.coverage_xml)


if __name__ == "__main__":
    sys.exit(main())
