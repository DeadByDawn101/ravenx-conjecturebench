#!/usr/bin/env python3
"""LEAN-FIRE: Lean Formal-Informal REasoning engine on MLX.

Implements the two-stage hybrid reasoning from Sivakumar et al. (2025):
1. Chain-of-Thought (CoT) - informal math reasoning in natural language
2. Lean-of-Thought (LoT) - formal translation into Lean 4 snippets

Then generates a conjecture and full autoformalisation.

Usage:
    python src/lean_fire.py \
        --model mlx-community/Qwen3-8B-4bit \
        --dataset data/conjecturebench.json \
        --output results/lean_fire_results.json
"""

import argparse
import json
import time
from pathlib import Path
from typing import Optional

try:
    import mlx.core as mx
    from mlx_lm import load, generate
    HAS_MLX = True
except ImportError:
    HAS_MLX = False


def strip_think_blocks(text: str) -> str:
    """Strip Qwen3's <think>...</think> reasoning blocks from output.
    
    Qwen3 wraps internal reasoning in <think> tags by default.
    We want the reasoning for logging but need clean output for
    Lean code extraction.
    """
    import re
    # Extract everything after the last </think> tag
    parts = re.split(r'</think>', text, flags=re.DOTALL)
    if len(parts) > 1:
        # Return content after final </think>, stripped
        clean = parts[-1].strip()
        return clean if clean else text.strip()
    # No think tags found — return as-is
    return text.strip()


COT_SYSTEM = (
    "You are an advanced assistant specializing in formal mathematics and "
    "Lean 4 theorem proving. You have extensive expertise in translating "
    "mathematical concepts from natural language into precise Lean 4 code."
)

COT_USER = """Using the provided informal statement, write a concise sequence of hints \
that guides the reader towards a formal statement in Lean.

Guidelines:
- Do not include any Lean code.
- Hints must be succinct and use mathematical notation.
- Do not include proof steps.
- Ensure all variables, functions, and assumptions are clearly introduced.

{few_shot}

**Informal statement**
{statement}

**Hints**"""

LOT_USER = """Using the provided hints, write Lean4 code snippets for each hint when \
appropriate to guide the reader towards a formal statement in Lean.

Guidelines:
- Do not provide formal proofs or imports.
- Match the hints to the Lean hints.

{few_shot}

**Informal statement**
{statement}

**Hints**
{cot}

**Lean Hints**"""

CONJECTURE_SYSTEM = (
    "You are an advanced assistant specializing in formal mathematics and "
    "Lean 4 theorem proving. You do not provide proofs or full theorem "
    "statements, only the mathematical expression representing the "
    "solution, proposition, or value being asserted."
)

CONJECTURE_USER = """Extract the mathematical solution as a Lean 4 expression.

1. Analyze the informal problem statement.
2. Provide the final solution as a single Lean 4 expression.

**Informal statement**
{statement}

```lean
abbrev solution"""

AUTOFORMALISE_USER = """Translate the following into a formal Lean 4 theorem.
Write only valid Lean 4 code. No proof or imports. Faithfully capture the meaning.

{hints}

**Name**
{name}

**Informal statement**
{statement}

Output:
```lean
theorem {name}"""


class LeanFireEngine:
    """LEAN-FIRE inference engine using MLX for local Apple Silicon."""

    def __init__(self, model_path: str, max_tokens: int = 2048):
        if not HAS_MLX:
            raise ImportError("MLX required. pip install mlx mlx-lm")
        print(f"Loading model: {model_path}")
        self.model, self.tokenizer = load(model_path)
        self.max_tokens = max_tokens
        self.few_shot = self._load_seeds()
        print("Model loaded. Ready for LEAN-FIRE.")

    def _load_seeds(self) -> str:
        seed_path = Path(__file__).parent.parent / "data" / "seed_examples.json"
        if seed_path.exists():
            with open(seed_path) as f:
                examples = json.load(f)
            return "\n\n".join(
                f"EXAMPLE {i+1}:\n**Informal statement**\n{ex['informal']}\n"
                f"**Hints**\n{ex['cot']}"
                for i, ex in enumerate(examples)
            )
        return ""

    def _gen(self, system: str, user: str, strip_think: bool = True) -> str:
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        raw = generate(
            self.model, self.tokenizer, prompt=prompt,
            max_tokens=self.max_tokens, verbose=False,
        )
        return strip_think_blocks(raw) if strip_think else raw

    def chain_of_thought(self, statement: str) -> str:
        return self._gen(COT_SYSTEM, COT_USER.format(
            few_shot=self.few_shot, statement=statement))

    def lean_of_thought(self, statement: str, cot: str) -> str:
        return self._gen(COT_SYSTEM, LOT_USER.format(
            few_shot=self.few_shot, statement=statement, cot=cot))

    def generate_conjecture(self, statement: str) -> str:
        return self._gen(CONJECTURE_SYSTEM,
                        CONJECTURE_USER.format(statement=statement))

    def autoformalise(self, statement: str, name: str,
                     hints: str = "", conjecture: Optional[str] = None) -> str:
        hint_block = f"\n**Combined Hints**\n{hints}\n" if hints else ""
        if conjecture:
            hint_block += f"\nimport Mathlib\n{conjecture}\n"
        return self._gen(COT_SYSTEM, AUTOFORMALISE_USER.format(
            hints=hint_block, name=name, statement=statement))

    def _interleave(self, cot: str, lot: str) -> str:
        cot_lines = [l.strip() for l in cot.strip().split("\n") if l.strip()]
        lot_lines = [l.strip() for l in lot.strip().split("\n") if l.strip()]
        combined = []
        for i, cl in enumerate(cot_lines):
            combined.append(cl)
            if i < len(lot_lines):
                combined.append(f"Lean: {lot_lines[i]}")
        for r in lot_lines[len(cot_lines):]:
            combined.append(f"Lean: {r}")
        return "\n".join(combined)

    def run(self, statement: str, name: str,
            seen_conjecture: Optional[str] = None) -> dict:
        """Full LEAN-FIRE pipeline."""
        t0 = time.time()
        cot = self.chain_of_thought(statement)
        lot = self.lean_of_thought(statement, cot)
        combined = self._interleave(cot, lot)
        gen_conj = None if seen_conjecture else self.generate_conjecture(statement)
        conj = seen_conjecture or gen_conj
        formal = self.autoformalise(statement, name, combined, conj)

        return {
            "theorem_name": name,
            "informal_statement": statement,
            "cot": cot, "lot": lot,
            "combined_hints": combined,
            "generated_conjecture": gen_conj,
            "seen_conjecture": seen_conjecture,
            "formalisation": formal,
            "elapsed_seconds": round(time.time() - t0, 2),
        }

    def _gen_with_reasoning(self, system: str, user: str) -> tuple:
        """Generate and return (clean_output, raw_with_thinking)."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        raw = generate(
            self.model, self.tokenizer, prompt=prompt,
            max_tokens=self.max_tokens, verbose=False,
        )
        return strip_think_blocks(raw), raw


def main():
    p = argparse.ArgumentParser(description="LEAN-FIRE on MLX")
    p.add_argument("--model", required=True)
    p.add_argument("--dataset", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--setting", choices=["seen", "unseen"], default="unseen")
    p.add_argument("--max-tokens", type=int, default=2048)
    p.add_argument("--limit", type=int, default=None)
    args = p.parse_args()

    engine = LeanFireEngine(args.model, args.max_tokens)

    with open(args.dataset) as f:
        dataset = json.load(f)
    if args.limit:
        dataset = dataset[:args.limit]

    results = []
    for i, prob in enumerate(dataset):
        print(f"[{i+1}/{len(dataset)}] {prob.get('name', '?')}...", end=" ", flush=True)
        seen = prob.get("conjecture") if args.setting == "seen" else None
        r = engine.run(prob["informal_statement"], prob.get("name", f"p_{i}"), seen)
        results.append(r)
        print(f"done ({r['elapsed_seconds']}s)")

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {len(results)} results to {args.output}")


if __name__ == "__main__":
    main()
