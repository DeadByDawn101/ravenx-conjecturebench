#!/usr/bin/env python3
"""Evaluation metrics for ConjectureBench: ConJudge, equiv_rfl, Typecheck.

Usage:
    python src/evaluate.py \
        --results results/lean_fire_results.json \
        --metrics conjudge equiv_rfl typecheck
"""

import argparse
import json
import subprocess
from pathlib import Path
from typing import Optional


def typecheck_lean(code: str, lean_path: str = "lean") -> bool:
    """Check if Lean 4 code typechecks."""
    full_code = f"import Mathlib\n\n{code}\n"
    try:
        result = subprocess.run(
            [lean_path, "--stdin"], input=full_code,
            capture_output=True, text=True, timeout=60,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def equiv_rfl(gold: str, generated: str, lean_path: str = "lean") -> bool:
    """Check definitional equivalence via Lean rfl tactic (Appendix B.4)."""
    gen_clean = generated.strip()
    if "abbrev solution" in gen_clean:
        gen_clean = gen_clean.replace("abbrev solution", "abbrev conjecture_generated :")

    code = f"""import Mathlib

{gold.strip()}

{gen_clean}

theorem equiv_check : conjecture_gold = conjecture_generated := by rfl
"""
    return typecheck_lean(code, lean_path)


def conjudge(
    formalisation: str, gold_conjecture: str,
    gold_formalisation: str, judge_model: Optional[str] = None,
) -> bool:
    """ConJudge: LLM-as-judge for conjecture presence in formalisation."""
    if judge_model:
        try:
            from mlx_lm import load, generate
            model, tok = load(judge_model)
            prompt = (
                f"Does this formal statement contain the conjecture?\n\n"
                f"Conjecture:\n```lean\n{gold_conjecture}\n```\n\n"
                f"Ground Truth:\n```lean\n{gold_formalisation}\n```\n\n"
                f"Statement to evaluate:\n```lean\n{formalisation}\n```\n\n"
                f"Answer True or False."
            )
            messages = [{"role": "user", "content": prompt}]
            formatted = tok.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True)
            resp = generate(model, tok, prompt=formatted,
                          max_tokens=256, verbose=False)
            return "true" in resp.lower()
        except Exception:
            pass

    # Fallback: substring match on conjecture value
    if ":=" in gold_conjecture:
        val = gold_conjecture.strip().split(":=")[-1].strip()
        return val in formalisation if val else False
    return False


def evaluate_results(results_path: str, metrics: list, lean_path: str = "lean"):
    """Run evaluation metrics on results."""
    with open(results_path) as f:
        results = json.load(f)

    scores = {m: {"pass_1": 0, "total": 0} for m in metrics}

    for r in results:
        for m in metrics:
            scores[m]["total"] += 1
            if m == "typecheck":
                if typecheck_lean(r.get("formalisation", ""), lean_path):
                    scores[m]["pass_1"] += 1
            elif m == "equiv_rfl":
                gold = r.get("gold_conjecture", "")
                gen = r.get("generated_conjecture", "")
                if gold and gen and equiv_rfl(gold, gen, lean_path):
                    scores[m]["pass_1"] += 1
            elif m == "conjudge":
                if conjudge(
                    r.get("formalisation", ""),
                    r.get("gold_conjecture", ""),
                    r.get("gold_formalisation", ""),
                ):
                    scores[m]["pass_1"] += 1

    print("\n" + "=" * 60)
    print("  ConjectureBench Evaluation Results")
    print("=" * 60)
    for m, s in scores.items():
        rate = (s["pass_1"] / s["total"] * 100) if s["total"] else 0
        print(f"  {m:12s}: {s['pass_1']:4d}/{s['total']:4d} ({rate:.1f}%)")
    print("=" * 60)
    return scores


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--results", required=True)
    p.add_argument("--metrics", nargs="+",
                   default=["conjudge", "equiv_rfl", "typecheck"])
    p.add_argument("--lean-path", default="lean")
    args = p.parse_args()
    evaluate_results(args.results, args.metrics, args.lean_path)


if __name__ == "__main__":
    main()
