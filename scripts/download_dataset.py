#!/usr/bin/env python3
"""Download ConjectureBench dataset from Huawei Noah's Ark Lab GitHub."""

import shutil
import subprocess
from pathlib import Path


def main():
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    repo_dir = Path("/tmp/ConjectureBench")

    print("Cloning ConjectureBench...")
    if repo_dir.exists():
        shutil.rmtree(repo_dir)

    subprocess.run(
        ["git", "clone", "--depth", "1",
         "https://github.com/huawei-noah/ConjectureBench.git",
         str(repo_dir)],
        check=True,
    )

    for pattern in ["*.json", "*.jsonl"]:
        for f in repo_dir.rglob(pattern):
            dest = data_dir / f.name
            shutil.copy2(f, dest)
            print(f"  {f.name} -> {dest}")

    seed_dir = repo_dir / "data" / "seed_examples"
    if seed_dir.exists():
        shutil.copytree(seed_dir, data_dir / "seed_examples", dirs_exist_ok=True)

    print(f"\nDataset in {data_dir}/")
    for f in sorted(data_dir.iterdir()):
        if f.is_file():
            print(f"  {f.name:40s} {f.stat().st_size:>10,d} bytes")


if __name__ == "__main__":
    main()
