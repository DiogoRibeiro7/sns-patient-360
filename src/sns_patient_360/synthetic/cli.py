"""Command-line interface for exporting deterministic synthetic clinical data."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from sns_patient_360.synthetic.export import export_journey
from sns_patient_360.synthetic.generator import generate_journey


def build_parser() -> argparse.ArgumentParser:
    """Build the synthetic data export command parser."""
    parser = argparse.ArgumentParser(
        prog="sns360-synthetic",
        description="Export independent synthetic clinical source bundles.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=360,
        help="Deterministic journey seed (default: 360).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("synthetic/generated"),
        help="Directory for source-specific JSON bundles.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Generate and export one deterministic synthetic patient journey."""
    parser = build_parser()
    args = parser.parse_args(argv)

    seed = args.seed
    output_dir = args.output_dir
    if not isinstance(seed, int):
        raise TypeError("parsed seed must be an int")
    if not isinstance(output_dir, Path):
        raise TypeError("parsed output directory must be a Path")

    created = export_journey(generate_journey(seed=seed), output_dir)
    for path in created:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
