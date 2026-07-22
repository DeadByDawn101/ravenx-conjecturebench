#!/usr/bin/env python3
"""Download and unify 5 HF datasets into ConjectureBench format.

Sources:
  1. Tonic/MiniF2F (488 problems, AMC/AIME/IMO)
  2. amitayusht/PutnamBench (1300+ Putnam competition)
  3. AI-MO/NuminaMath-LEAN (100K Lean 4 statements)
  4. AI-MO/minif2f_test (244 corrected formalisations)
  5. InternLM/Lean-GitHub (compiled Lean repos)

Output: data/unified_bench.json — all problems in ConjectureBench format:
  {name, informal_statement, formal_statement, conjecture, source, solution_type}
"""

import json
import re
import sys
from pathlib import Path

try:
    from datasets import load_dataset
except ImportError:
    print("Install: pip install datasets")
    sys.exit(1)


def extract_conjecture_from_formal(formal: str) -> str:
    """Try to extract the conjecture/answer from a formal Lean 4 statement.

    Looks for patterns like:
      `: x = 26`  (numerical answer embedded in conclusion)
      `abbrev conjecture`  (explicit conjecture definition)
      `:= sorry`  (the goal before sorry)
    """
    # Pattern 1: abbrev conjecture/solution
    m = re.search(r'(abbrev\s+(?:conjecture|solution)\s*.*)', formal)
    if m:
        return m.group(1).strip()

    # Pattern 2: conclusion before := sorry (last `:` clause)
    # e.g., `: x = 26 := by` → conjecture is "26"
    m = re.search(r':\s*(.+?)\s*:=\s*(?:by|sorry)', formal, re.DOTALL)
    if m:
        conclusion = m.group(1).strip()
        # Try to extract a numeric answer
        num = re.search(r'=\s*(\d+)', conclusion)
        if num:
            return f"abbrev conjecture : ℕ := {num.group(1)}"
        return f"-- conclusion: {conclusion[:200]}"

    return ""


def classify_solution_type(conjecture: str, informal: str) -> str:
    """Classify as numerical, algebraic, or proof."""
    if not conjecture:
        return "proof"
    if re.search(r':=\s*\d+\s*$', conjecture):
        return "numerical"
    if "Prop" in conjecture or "True" in conjecture or "False" in conjecture:
        return "proof"
    return "algebraic"


def load_minif2f_tonic():
    """Source 1: Tonic/MiniF2F — 488 problems."""
    print("Loading Tonic/MiniF2F...")
    problems = []
    try:
        for split in ["validation", "test"]:
            try:
                ds = load_dataset("Tonic/MiniF2F", split=split)
                for row in ds:
                    informal = row.get("informal_prefix", "")
                    formal = row.get("formal_statement", "")
                    name = row.get("name", f"minif2f_{len(problems)}")
                    if not informal or not formal:
                        continue
                    conj = extract_conjecture_from_formal(formal)
                    problems.append({
                        "name": name,
                        "informal_statement": informal.strip(),
                        "formal_statement": formal.strip(),
                        "conjecture": conj,
                        "solution_type": classify_solution_type(conj, informal),
                        "source": "Tonic/MiniF2F",
                        "split": split,
                    })
            except Exception as e:
                print(f"  Warning: split '{split}' failed: {e}")
        print(f"  Loaded {len(problems)} from Tonic/MiniF2F")
    except Exception as e:
        print(f"  ERROR loading Tonic/MiniF2F: {e}")
    return problems


def load_putnambench():
    """Source 2: amitayusht/PutnamBench — 1300+ Putnam problems."""
    print("Loading amitayusht/PutnamBench...")
    problems = []
    try:
        ds = load_dataset("amitayusht/PutnamBench", split="train")
        for row in ds:
            informal = row.get("informal_statement", row.get("informal_prefix", ""))
            formal = row.get("formal_statement", "")
            name = row.get("name", row.get("id", f"putnam_{len(problems)}"))
            if not formal:
                continue
            conj = extract_conjecture_from_formal(formal)
            problems.append({
                "name": name,
                "informal_statement": informal.strip() if informal else "",
                "formal_statement": formal.strip(),
                "conjecture": conj,
                "solution_type": classify_solution_type(conj, informal or ""),
                "source": "amitayusht/PutnamBench",
                "split": "train",
            })
        print(f"  Loaded {len(problems)} from amitayusht/PutnamBench")
    except Exception as e:
        print(f"  ERROR loading PutnamBench: {e}")
    return problems


def load_numina_lean():
    """Source 3: AI-MO/NuminaMath-LEAN — 100K problems (sample 2000)."""
    print("Loading AI-MO/NuminaMath-LEAN (sampling 2000)...")
    problems = []
    try:
        ds = load_dataset("AI-MO/NuminaMath-LEAN", split="train")
        # Sample to keep manageable — full set is 100K+
        indices = list(range(0, len(ds), max(1, len(ds) // 2000)))[:2000]
        for i in indices:
            row = ds[i]
            informal = row.get("informal_statement", row.get("problem", ""))
            formal = row.get("formal_statement", "")
            name = row.get("name", row.get("id", f"numina_{i}"))
            if not formal:
                continue
            conj = extract_conjecture_from_formal(formal)
            problems.append({
                "name": str(name),
                "informal_statement": str(informal).strip() if informal else "",
                "formal_statement": formal.strip(),
                "conjecture": conj,
                "solution_type": classify_solution_type(conj, str(informal) if informal else ""),
                "source": "AI-MO/NuminaMath-LEAN",
                "split": "train",
            })
        print(f"  Loaded {len(problems)} from AI-MO/NuminaMath-LEAN")
    except Exception as e:
        print(f"  ERROR loading NuminaMath-LEAN: {e}")
    return problems


def load_minif2f_corrected():
    """Source 4: AI-MO/minif2f_test — 244 corrected formalisations."""
    print("Loading AI-MO/minif2f_test...")
    problems = []
    try:
        ds = load_dataset("AI-MO/minif2f_test", split="test")
        for row in ds:
            informal = row.get("informal_prefix", row.get("informal_statement", ""))
            formal = row.get("formal_statement", "")
            name = row.get("name", row.get("id", f"minif2f_corrected_{len(problems)}"))
            if not formal:
                continue
            conj = extract_conjecture_from_formal(formal)
            problems.append({
                "name": name,
                "informal_statement": str(informal).strip() if informal else "",
                "formal_statement": formal.strip(),
                "conjecture": conj,
                "solution_type": classify_solution_type(conj, str(informal) if informal else ""),
                "source": "AI-MO/minif2f_test",
                "split": "test",
            })
        print(f"  Loaded {len(problems)} from AI-MO/minif2f_test")
    except Exception as e:
        print(f"  ERROR loading minif2f_test: {e}")
    return problems


def load_lean_github():
    """Source 5: InternLM/Lean-GitHub — compiled Lean repos (sample 1000)."""
    print("Loading InternLM/Lean-GitHub (sampling 1000)...")
    problems = []
    try:
        ds = load_dataset("InternLM/Lean-GitHub", split="train")
        indices = list(range(0, len(ds), max(1, len(ds) // 1000)))[:1000]
        for i in indices:
            row = ds[i]
            formal = row.get("formal_statement", row.get("code", ""))
            name = row.get("name", row.get("full_name", f"lean_github_{i}"))
            if not formal:
                continue
            problems.append({
                "name": str(name),
                "informal_statement": "",  # Lean-GitHub has no informal statements
                "formal_statement": str(formal).strip()[:2000],
                "conjecture": "",
                "solution_type": "proof",
                "source": "InternLM/Lean-GitHub",
                "split": "train",
            })
        print(f"  Loaded {len(problems)} from InternLM/Lean-GitHub")
    except Exception as e:
        print(f"  ERROR loading Lean-GitHub: {e}")
    return problems


def deduplicate(problems: list) -> list:
    """Remove duplicate problems by name."""
    seen = set()
    unique = []
    for p in problems:
        key = p["name"]
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def main():
    print("=" * 60)
    print("  RavenX-ConjectureBench — Unified Dataset Builder")
    print("=" * 60)
    print()

    all_problems = []

    # Load all 5 sources
    all_problems.extend(load_minif2f_tonic())
    all_problems.extend(load_putnambench())
    all_problems.extend(load_numina_lean())
    all_problems.extend(load_minif2f_corrected())
    all_problems.extend(load_lean_github())

    # Deduplicate
    before = len(all_problems)
    all_problems = deduplicate(all_problems)
    after = len(all_problems)

    # Stats
    print()
    print("=" * 60)
    print("  Dataset Summary")
    print("=" * 60)
    sources = {}
    types = {}
    has_informal = 0
    has_conjecture = 0
    for p in all_problems:
        src = p["source"]
        sources[src] = sources.get(src, 0) + 1
        st = p["solution_type"]
        types[st] = types.get(st, 0) + 1
        if p["informal_statement"]:
            has_informal += 1
        if p["conjecture"]:
            has_conjecture += 1

    print(f"  Total problems:    {len(all_problems)}")
    print(f"  Deduplicated:      {before - after} removed")
    print(f"  With informal:     {has_informal}")
    print(f"  With conjecture:   {has_conjecture}")
    print()
    print("  By source:")
    for src, count in sorted(sources.items()):
        print(f"    {src:35s} {count:6d}")
    print()
    print("  By solution type:")
    for st, count in sorted(types.items()):
        print(f"    {st:15s} {count:6d}")

    # Save unified dataset
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Full unified set
    with open(data_dir / "unified_bench.json", "w") as f:
        json.dump(all_problems, f, indent=2, ensure_ascii=False)
    print(f"\n  Saved: data/unified_bench.json ({len(all_problems)} problems)")

    # ConjectureBench-compatible subset (has informal + formal + conjecture)
    conjecture_ready = [
        p for p in all_problems
        if p["informal_statement"] and p["conjecture"]
    ]
    with open(data_dir / "conjecturebench.json", "w") as f:
        json.dump(conjecture_ready, f, indent=2, ensure_ascii=False)
    print(f"  Saved: data/conjecturebench.json ({len(conjecture_ready)} conjecture-ready)")

    # Quick-test subset (first 50 conjecture-ready)
    with open(data_dir / "quick_test.json", "w") as f:
        json.dump(conjecture_ready[:50], f, indent=2, ensure_ascii=False)
    print(f"  Saved: data/quick_test.json (50 for smoke testing)")

    print()
    print("=" * 60)
    print("  Done. Run LEAN-FIRE with:")
    print("    python src/lean_fire.py \\")
    print("      --model mlx-community/Qwen3-8B-4bit \\")
    print("      --dataset data/quick_test.json \\")
    print("      --output results/smoke_test.json \\")
    print("      --limit 5")
    print("=" * 60)


if __name__ == "__main__":
    main()
