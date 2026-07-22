# RavenX-ConjectureBench

**An MLX-native implementation of conjecture generation and autoformalisation
evaluation for Apple Silicon, built on the ConjectureBench framework.**

Patent Pending — RavenX AI Labs LLC

## What Is This?

ConjectureBench (Sivakumar et al., 2025, arXiv:2510.11986) identified a
critical overlooked step in formal mathematical reasoning: conjecturing.
Before a model can autoformalise a mathematical statement into Lean 4, it
must first conjecture the answer — an explicit value, bound, or
proposition. Current LLMs fail dramatically when this step isn't
pre-supplied: performance drops ~52 percentage points when conjectures are
withheld.

This repo takes the ConjectureBench insight and builds an MLX-native
pipeline for Apple Silicon that:

1. **Runs ConjectureBench evaluation locally** on M4 Max / M-series Macs
   without GPU cloud dependency
2. **Implements LEAN-FIRE** (Lean Formal-Informal REasoning) as an
   MLX-served inference pipeline with Chain-of-Thought + Lean-of-Thought
   interleaving
3. **Fine-tunes conjecture generation** using MLX-LM LoRA on the
   ConjectureBench dataset to improve standalone conjecture capabilities
4. **Integrates with RavenX CyberAgent** for security-domain formal
   reasoning (proving security properties of protocols, cryptographic
   constructions, etc.)

## Why MLX?

The paper evaluated only GPT-4.1 and DeepSeek-V3.1 via API. No local
inference, no fine-tuning, no Apple Silicon. This repo fills that gap:

- **MLX-LM** for fast local inference on M-series (89+ tok/s on M4 Max)
- **MLX LoRA** for parameter-efficient fine-tuning of conjecture
  generation capabilities
- **No cloud dependency** — all evaluation runs locally
- **Private math reasoning** — your conjectures never leave your machine

## Architecture

```
┌─────────────────────────────────────┐
│        Informal Math Problem        │
└──────────────┬──────────────────────┘
               │
    ┌──────────▼──────────┐
    │   LEAN-FIRE Engine  │
    │  (MLX-served model) │
    │                     │
    │  1. Chain-of-Thought│ ← informal reasoning (natural language)
    │  2. Lean-of-Thought │ ← formal translation (Lean 4 snippets)
    │  3. Conjecture Gen  │ ← candidate solution generation
    │  4. Autoformalise   │ ← full Lean 4 statement
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │   Lean 4 Verifier   │
    │  (Typecheck + BEq+) │
    └──────────┬──────────┘
               │
    ┌──────────▼──────────┐
    │   ConJudge + equiv  │
    │   (evaluation)      │
    └─────────────────────┘
```

## Key Innovation: Security-Domain Formal Reasoning

While ConjectureBench targets competition mathematics (Putnam, combinatorics),
RavenX extends the conjecture-then-formalise pipeline to security domains:

- **Proving protocol correctness** — conjecture security properties of
  cryptographic protocols, then formalise in Lean 4
- **Formal verification of smart contracts** — conjecture invariants,
  autoformalise, prove
- **Sovereignty Chain integration** — formal proofs that the
  cryptographic chain properties hold (gradient ledger integrity,
  watermark unforgability, refusal direction encryption completeness)

This bridges the ConjectureBench methodology with RavenX's core mission
of sovereign AI infrastructure and model IP protection.

## Dataset

### Unified Benchmark (5 HF Sources)

The original ConjectureBench (Huawei Noah's Ark Lab) is not yet public.
We built a unified replacement from 5 HuggingFace datasets covering
the same problem space:

| Source | Problems | Content |
|--------|----------|---------|
| **Tonic/MiniF2F** | ~488 | AMC/AIME/IMO, informal + Lean 4 pairs |
| **amitayusht/PutnamBench** | ~1300 | Putnam Competition 1965-2023, Lean 4 |
| **AI-MO/NuminaMath-LEAN** | 2000 (sampled from 100K) | Competition math, Lean 4 + proofs |
| **AI-MO/minif2f_test** | ~244 | Corrected MiniF2F formalisations |
| **InternLM/Lean-GitHub** | 1000 (sampled) | Compiled GitHub Lean repos |

Total: ~5,000+ unified problems in ConjectureBench format.

Run `python scripts/download_dataset.py` to pull all sources and
generate:
- `data/unified_bench.json` — all problems
- `data/conjecturebench.json` — conjecture-ready subset (has informal + conjecture)
- `data/quick_test.json` — 50 problems for smoke testing

### RavenX Security Conjectures (downstream, in progress)
- Security protocol properties formalised in Lean 4
- Cryptographic construction correctness conjectures
- Sovereignty Chain formal verification targets

## Quick Start

### Prerequisites
- Python 3.11+ on Apple Silicon Mac
- MLX + MLX-LM installed
- Lean 4 (via elan) for verification

### Install

```bash
# Clone
git clone https://github.com/DeadByDawn101/ravenx-conjecturebench.git
cd ravenx-conjecturebench

# Create venv
python3 -m venv .venv
source .venv/bin/activate

# Install deps
pip install -e .
```

### Run Evaluation

```bash
# Download all 5 HF datasets and build unified benchmark
pip install datasets
python scripts/download_dataset.py

# Run LEAN-FIRE conjecture generation (local MLX inference)
python src/lean_fire.py \
  --model mlx-community/Qwen3-8B-4bit \
  --dataset data/conjecturebench.json \
  --output results/lean_fire_qwen3_8b.json

# Evaluate with ConJudge + equiv_rfl
python src/evaluate.py \
  --results results/lean_fire_qwen3_8b.json \
  --metrics conjudge equiv_rfl typecheck
```

### Fine-tune Conjecture Generation

```bash
# Prepare LoRA training data from ConjectureBench
python scripts/prepare_training_data.py \
  --dataset data/conjecturebench.json \
  --output data/conjecture_train.jsonl

# Train with MLX LoRA
python src/train_conjecture.py \
  --model mlx-community/Qwen3-8B-4bit \
  --data data/conjecture_train.jsonl \
  --output models/conjecture-lora \
  --iters 500 \
  --lora-rank 16
```

## Metrics

| Metric | What It Measures |
|--------|-----------------|
| **ConJudge** | LLM-as-judge: is the gold conjecture correctly incorporated in the autoformalised statement? |
| **equiv_rfl** | Lean tactic `rfl`: is the generated conjecture definitionally equivalent to the gold? |
| **Typecheck** | Does the generated Lean 4 code compile without error? |
| **BEq+** | Lean-tactic-based semantic equivalence (strict) |
| **LLM Grader** | Back-translate to NL then judge semantic equivalence |

## Related Work

### Core Papers
- Sivakumar et al. (2025). "Conjecturing: An Overlooked Step in Formal
  Mathematical Reasoning." arXiv:2510.11986
- Tsoukalas et al. (2024). "PutnamBench." NeurIPS 2024.
  github.com/trishullab/PutnamBench
- Liu et al. (2025). "CombiBench." arXiv:2505.03171

### Theorem Proving Systems
- AlphaProof (DeepMind) — RL-based, IMO 2024 silver/2025 gold
- SeedProver (Luoxin Chen et al., 2025) — lemma-style whole-proof, IMO 2025 gold
- Aristotle — formal verification + informal reasoning hybrid
- Kimina-Prover (Wang et al., 2025) — RL for formal reasoning
- DeepSeek-Prover-V2 — RL + subgoal decomposition
- Goedel-Prover — open-source ATP trained on synthetic formal data
- TheoremLlama (Wang et al., 2024) — general LLM → Lean 4 expert

### Formal Reasoning Approaches
- Draft-Sketch-Prove (Jiang et al., 2023) — informal proofs → formal
- LEAN-GitHub — compiled GitHub Lean repos for training
- Lean Copilot (Song et al., 2024) — LLM copilot for Lean
- MA-LoT (Wang et al., 2025) — multi-agent Lean reasoning
- CriticLean (Peng et al., 2025) — critic-guided RL for formalisation

### MLX + Apple Silicon
- MLX-LM — Apple's ML framework for local LLM inference
- MLX LoRA — parameter-efficient fine-tuning on Apple Silicon

## License

Apache 2.0 with reservation of patent rights.

## About

RavenX AI Labs LLC — Gabriel Garcia, San Jose, CA
- USPTO Provisional #64/104,760 (Sovereignty Chain)
- USPTO Provisional #64/087,357 (Soul Infusion)
- GitHub: @DeadByDawn101
- HuggingFace: deadbydawn101

---

*"Walls break. Math doesn't." — RavenX AI Labs*
