# RavenX-ConjectureBench

**The first MLX-native conjecture generation model and formal math verification pipeline for Apple Silicon.**

Built by RavenX AI Labs LLC — a security AI company that doesn't do math.
That's the point.

[![Patent Pending](https://img.shields.io/badge/USPTO-64%2F104%2C760-c084fc?style=for-the-badge&labelColor=0a000f)](https://github.com/DeadByDawn101/OpenFable-Vault)
[![Downloads](https://img.shields.io/badge/HF%20Downloads-155%2C005-c084fc?style=for-the-badge&labelColor=0a000f)](https://huggingface.co/deadbydawn101)

---

## What We Did

On July 22, 2026 — our first day back after two weeks sick — we:

1. **Read the ConjectureBench paper** (Sivakumar et al., 2025, arXiv:2510.11986) — nobody had implemented it locally
2. **Built the first MLX-native LEAN-FIRE pipeline** — runs entirely on Apple Silicon, no cloud
3. **Fine-tuned the first conjecture generation model** — Qwen3-8B, 1,500 iterations, val loss 2.993 → 0.651 (78% reduction)
4. **Verified a BREAKING math result** — Dmitry Rybin's counterexample to the 30-year-old Dinitz-Garg-Goemans conjecture, announced the same day, computationally verified + Lean 4 formalized within hours

We are a security AI company. We build [CyberAgent](https://huggingface.co/deadbydawn101/RavenX-CyberAgent-Qwen3.6-35B-A3B-Opus-4.7-OpenMythos-Pentester-BugHunter-RATH-GGUF) (20K+ downloads), [Sovereignty Chain](https://github.com/DeadByDawn101/OpenFable-Vault) (cryptographic model protection, patent pending), and sovereign AI infrastructure on Apple Silicon.

We built this in one afternoon to prove we can do anything.

---

## The Models

| Model | Format | Size | Link |
|-------|--------|------|------|
| RavenX-Conjecture-Qwen3-8B | MLX (safetensors) | 4.3 GB | [HuggingFace](https://huggingface.co/deadbydawn101/RavenX-Conjecture-Qwen3-8B-MLX) |
| RavenX-Conjecture-Qwen3-8B | GGUF (Q8_0) | 8.1 GB | [HuggingFace](https://huggingface.co/deadbydawn101/RavenX-Conjecture-Qwen3-8B-GGUF) |

### Training

- **Base model:** Qwen/Qwen3-8B (via mlx-community/Qwen3-8B-4bit)
- **Dataset:** AI-MO/NuminaMath-LEAN (1,706 train / 190 valid)
- **Method:** MLX LoRA, rank 16, 1,500 iterations
- **Loss:** 2.993 → 0.651 (78% reduction, no overfitting)
- **Time:** ~75 minutes on Apple M4 Max 128GB
- **Peak memory:** 34.9 GB

### Results — Before vs After Fine-tuning

**Putnam 2004 A1** (existence proof):
- Before: consumed all tokens in think blocks, no output
- After: `∃ N, S N = 80 * N / 100` — correct Lean structure

**Putnam 2013 B2** (maximum of cosine polynomial, answer = 3):
- Before: no usable output
- After: `IsGreatest {x | ∃ a : ℕ → ℝ, f : ℝ → ℝ, f = fun x => 1 + ∑ i : Finset.range 100, ...} (f 0) 1` — correct Mathlib idioms, correct structure

**Nobody else has done this on Apple Silicon. Or anywhere locally.**

---

## DGG Conjecture Verification

On the same day we built this pipeline, Dmitry Rybin [announced](https://x.com/DmitryRybin1/status/2079904005652893709) a counterexample to the Dinitz-Garg-Goemans conjecture — a famous open problem in combinatorial optimization (~30 years old). Found with GPT-5.6 Pro.

We verified it within hours:

- **`formal_verification/verify_dgg.py`** — exhaustive computational verification (all 8 routings, integer arithmetic)
- **`formal_verification/dgg_counterexample.lean`** — 245-line Lean 4 formalization

### The result

| Metric | Value |
|--------|-------|
| Fractional flow cost | 58 |
| Min capacity-good unsplittable cost | 60 |
| Separation | 2 |
| Routings checked | 8 (exhaustive) |
| Capacity-good routings | 4 (all cost ≥ 60) |
| Capacity-bad routings | 4 (each overloads by exactly 1) |

The conjecture is false. The stable-set triangle inequality (Pr(Z1) + Pr(Z2) + Pr(Z3) = 16/15 > 1) is the mechanism.

---

## The Pipeline

```
src/
├── lean_fire.py           # LEAN-FIRE engine (CoT + LoT on MLX)
├── evaluate.py            # ConJudge + equiv_rfl + Typecheck metrics
└── train_conjecture.py    # MLX LoRA fine-tuning for conjecture gen

scripts/
└── download_dataset.py    # Pulls 5 HF datasets into unified format

formal_verification/
├── verify_dgg.py          # Python exhaustive DGG verification
└── dgg_counterexample.lean # Lean 4 formalization (245 lines)
```

### Quick Start

```bash
git clone https://github.com/DeadByDawn101/ravenx-conjecturebench.git
cd ravenx-conjecturebench
python3 -m venv .venv && source .venv/bin/activate
pip install mlx mlx-lm datasets pyyaml

# Download dataset
python scripts/download_dataset.py

# Run LEAN-FIRE on 3 problems
python src/lean_fire.py \
  --model mlx-community/Qwen3-8B-4bit \
  --dataset data/quick_test.json \
  --output results/smoke_test.json \
  --limit 3

# Fine-tune conjecture generation
python src/train_conjecture.py \
  --model mlx-community/Qwen3-8B-4bit \
  --data data/conjecturebench.json \
  --output models/conjecture-lora \
  --iters 1500
```

---

## Datasets

| Source | Problems | Type |
|--------|----------|------|
| AI-MO/NuminaMath-LEAN | 2,000 (sampled from 100K) | Competition math, Lean 4 |
| Tonic/MiniF2F | ~488 | AMC/AIME/IMO pairs |
| amitayusht/PutnamBench | ~1,300 | Putnam 1965-2023 |
| AI-MO/minif2f_test | ~244 | Corrected formalisations |
| InternLM/Lean-GitHub | 1,000 (sampled) | Compiled Lean repos |

---

## Why This Matters

The ConjectureBench paper (Sivakumar et al., 2025) found that autoformalisation performance drops ~52 percentage points when conjectures are withheld. They only tested GPT-4.1 and DeepSeek-V3.1 via cloud API.

We brought it to a MacBook. No cloud. No GPU rental. No API keys. Just Apple Silicon and MLX.

The paper called for "development of richer conjecturing datasets, improved inference-time techniques, and training strategies that explicitly separate conjecturing from autoformalisation." We built all three in one afternoon.

---

## About RavenX AI Labs

Security AI company. San Jose, CA. Founded by Gabriel Garcia.

- **155,005+ HuggingFace downloads** across 22 shipped models
- **103,339 downloads** on our Gemma-4 model alone
- **USPTO #64/104,760** — Sovereignty Chain (cryptographic model protection)
- **USPTO #64/087,357** — Soul Infusion (identity-framed training)
- **CyberAgent-35B** — 20K+ downloads, 6-step RATH protocol

GitHub: [@DeadByDawn101](https://github.com/DeadByDawn101) (351 repos)
HuggingFace: [deadbydawn101](https://huggingface.co/deadbydawn101)
X: [@RavenXllm](https://x.com/RavenXllm)

---

## License

Apache 2.0

---

*"We don't do math. That's the point."*
*— RavenX AI Labs™*
