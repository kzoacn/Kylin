#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import platform
import re
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BENCH_CSV = REPO_ROOT / "paper" / "data" / "package_bench.csv"
MEMORY_CSV = REPO_ROOT / "paper" / "data" / "package_memory.csv"
SUMMARY_MD = REPO_ROOT / "Implementations" / "benchmarks" / "summary.md"


def run(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def parse_kv(output: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def parse_size(output: str) -> tuple[int, int, int]:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if len(lines) < 2:
        raise RuntimeError("unexpected size output")
    fields = lines[1].split()
    return int(fields[0]), int(fields[1]), int(fields[2])


def parse_stack_usage(instance_dir: Path) -> tuple[int, str]:
    max_bytes = -1
    max_function = ""
    for su_path in sorted((instance_dir / ".stack-usage").glob("*.su")):
        for raw_line in su_path.read_text(encoding="utf-8").splitlines():
            fields = raw_line.split("\t")
            if len(fields) < 2:
                continue
            location = fields[0]
            match = re.match(r".*:(.*)$", location)
            function = match.group(1) if match else location
            try:
                stack_bytes = int(fields[1])
            except ValueError:
                continue
            if stack_bytes > max_bytes:
                max_bytes = stack_bytes
                max_function = function
    if max_bytes < 0:
        raise RuntimeError(f"no stack-usage data found in {instance_dir}")
    return max_bytes, max_function


def implementation_label(instance_dir: Path) -> str:
    if (
        "Reference_Implementation" in instance_dir.parts
        or "Additional_Implementation" in instance_dir.parts
    ):
        return "ref"
    return "opt"


def discover_instance_dirs(include_additional: bool = False) -> list[Path]:
    roots = [
        REPO_ROOT / "Implementations" / "Reference_Implementation",
        REPO_ROOT / "Implementations" / "Optimized_Implementation",
    ]
    if include_additional:
        roots.append(REPO_ROOT / "Implementations" / "Additional_Implementation")

    directories: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        directories.extend(
            sorted(
                path for path in root.glob("Kylin-*")
                if path.is_dir() and (path / "Makefile").is_file()
            )
        )
    return directories


def collect(include_additional: bool = False) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    bench_rows: list[dict[str, str]] = []
    memory_rows: list[dict[str, str]] = []
    instance_dirs = discover_instance_dirs(include_additional=include_additional)

    if not instance_dirs:
        raise RuntimeError("no Kylin instance directories found")

    for instance_dir in instance_dirs:
        impl = implementation_label(instance_dir)
        print(f"[metrics] collecting {impl} {instance_dir.name}", flush=True)

        run(["make", "clean"], instance_dir)
        bench_output = run(["make", "bench"], instance_dir)
        bench_values = parse_kv(bench_output)

        size_output = run(["size", "bench_sig"], instance_dir)
        text_bytes, data_bytes, bss_bytes = parse_size(size_output)

        run(["make", "stack_usage"], instance_dir)
        max_stack_bytes, max_stack_function = parse_stack_usage(instance_dir)
        run(["make", "clean"], instance_dir)

        bench_rows.append(
            {
                "name": bench_values["instance"],
                "impl": impl,
                "keygen_ms": bench_values["keygen_ms"],
                "sign_ms": bench_values["sign_ms"],
                "verify_ms": bench_values["verify_ms"],
                "pk": bench_values["pk_bytes"],
                "sk": bench_values["sk_bytes"],
                "sig": bench_values["sig_bytes"],
            }
        )
        memory_rows.append(
            {
                "name": bench_values["instance"],
                "impl": impl,
                "max_stack_bytes": str(max_stack_bytes),
                "max_stack_function": max_stack_function,
                "text_bytes": str(text_bytes),
                "data_bytes": str(data_bytes),
                "bss_bytes": str(bss_bytes),
            }
        )

    bench_rows.sort(key=lambda row: (row["name"], row["impl"]))
    memory_rows.sort(key=lambda row: (row["name"], row["impl"]))
    return bench_rows, memory_rows


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_summary(bench_rows: list[dict[str, str]], memory_rows: list[dict[str, str]]) -> None:
    SUMMARY_MD.parent.mkdir(parents=True, exist_ok=True)
    gcc_version = subprocess.run(
        ["gcc", "--version"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()[0]
    host = platform.platform()

    bench_index = {(row["name"], row["impl"]): row for row in bench_rows}

    lines = [
        "# Kylin Package Metrics",
        "",
        f"- Host: `{host}`",
        f"- Compiler: `{gcc_version}`",
        "- Benchmark method: host-local wall-clock milliseconds from the automated `bench_sig` driver on a 32-byte message.",
        "- Memory method: GCC `-fstack-usage` maximum single-frame stack report plus `size bench_sig` section sizes.",
        "",
        "| Instance | Impl | KeyGen (ms) | Sign (ms) | Verify (ms) | Max frame (bytes) | Max-frame function | .text | .data | .bss |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |",
    ]

    for memory_row in memory_rows:
        bench_row = bench_index[(memory_row["name"], memory_row["impl"])]
        lines.append(
            "| {name} | {impl} | {keygen_ms} | {sign_ms} | {verify_ms} | {max_stack_bytes} | `{max_stack_function}` | {text_bytes} | {data_bytes} | {bss_bytes} |".format(
                name=bench_row["name"],
                impl=bench_row["impl"],
                keygen_ms=bench_row["keygen_ms"],
                sign_ms=bench_row["sign_ms"],
                verify_ms=bench_row["verify_ms"],
                max_stack_bytes=memory_row["max_stack_bytes"],
                max_stack_function=memory_row["max_stack_function"],
                text_bytes=memory_row["text_bytes"],
                data_bytes=memory_row["data_bytes"],
                bss_bytes=memory_row["bss_bytes"],
            )
        )

    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Collect Kylin package benchmark and memory metrics."
    )
    parser.add_argument(
        "--include-additional",
        action="store_true",
        help="also collect reference-only q=2^24 Additional_Implementation instances",
    )
    args = parser.parse_args()

    try:
        bench_rows, memory_rows = collect(include_additional=args.include_additional)
        write_csv(
            BENCH_CSV,
            ["name", "impl", "keygenms", "signms", "verifyms", "pkbytes", "skbytes", "sigbytes"],
            [
                {
                    "name": row["name"],
                    "impl": row["impl"],
                    "keygenms": row["keygen_ms"],
                    "signms": row["sign_ms"],
                    "verifyms": row["verify_ms"],
                    "pkbytes": row["pk"],
                    "skbytes": row["sk"],
                    "sigbytes": row["sig"],
                }
                for row in bench_rows
            ],
        )
        write_csv(
            MEMORY_CSV,
            ["name", "impl", "maxstack", "textbytes", "databytes", "bssbytes", "maxstackfn"],
            [
                {
                    "name": row["name"],
                    "impl": row["impl"],
                    "maxstack": row["max_stack_bytes"],
                    "textbytes": row["text_bytes"],
                    "databytes": row["data_bytes"],
                    "bssbytes": row["bss_bytes"],
                    "maxstackfn": row["max_stack_function"],
                }
                for row in memory_rows
            ],
        )
        write_summary(bench_rows, memory_rows)
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stdout)
        sys.stderr.write(exc.stderr)
        return exc.returncode
    except Exception as exc:  # pragma: no cover - defensive script
        sys.stderr.write(f"{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
