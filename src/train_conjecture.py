#!/usr/bin/env python3
"""Fine-tune conjecture generation on ConjectureBench using MLX LoRA.

Addresses the standalone conjecture generation gap from the paper
(Table 4: ~3-5% equiv_rfl pass@1).

Usage:
    python src/train_conjecture.py \
        --model mlx-community/Qwen3-8B-4bit \
        --data data/conjecturebench.json \
        --output models/conjecture-lora \
        --iters 500 --lora-rank 16
"""

import argparse
import json
import subprocess
from pathlib import Path


def prepare_training_data(dataset_path: str, output_dir: str):
    """Convert ConjectureBench into MLX LoRA chat-format JSONL."""
    with open(dataset_path) as f:
        dataset = json.load(f)

    examples = []
    for prob in dataset:
        informal = prob.get("informal_statement", "")
        conjecture = prob.get("conjecture", "")
        if not informal or not conjecture:
            continue
        examples.append({
            "messages": [
                {"role": "system", "content": (
                    "You are an expert mathematician. Given an informal "
                    "mathematical problem, generate the precise solution "
                    "as a Lean 4 expression. Output only Lean 4 code."
                )},
                {"role": "user", "content": informal},
                {"role": "assistant", "content": conjecture},
            ]
        })

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    split = int(len(examples) * 0.9)
    train, valid = examples[:split], examples[split:]

    for name, data in [("train.jsonl", train), ("valid.jsonl", valid)]:
        with open(out / name, "w") as f:
            for ex in data:
                f.write(json.dumps(ex) + "\n")

    print(f"Train: {len(train)} examples")
    print(f"Valid: {len(valid)} examples")
    return str(out / "train.jsonl"), str(out / "valid.jsonl")


def train_lora(model: str, data_dir: str, output: str,
               iters: int = 500, lora_rank: int = 16,
               lr: float = 1e-5, batch: int = 4):
    """Run MLX LoRA fine-tuning."""
    cmd = [
        "python", "-m", "mlx_lm.lora",
        "--model", model,
        "--train",
        "--data", data_dir,
        "--adapter-path", output,
        "--iters", str(iters),
        "--lora-layers", "16",
        "--lora-rank", str(lora_rank),
        "--learning-rate", str(lr),
        "--batch-size", str(batch),
        "--val-batches", "25",
        "--steps-per-eval", "100",
        "--steps-per-report", "10",
        "--max-seq-length", "2048",
    ]
    print(f"MLX LoRA training: {model}, {iters} iters, rank {lora_rank}")
    subprocess.run(cmd, check=True)
    print(f"Adapter saved to {output}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--data", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--iters", type=int, default=500)
    p.add_argument("--lora-rank", type=int, default=16)
    p.add_argument("--learning-rate", type=float, default=1e-5)
    p.add_argument("--batch-size", type=int, default=4)
    p.add_argument("--prepare-only", action="store_true")
    args = p.parse_args()

    data = Path(args.data)
    if data.suffix == ".json":
        data_dir = Path(args.output).parent / "training_data"
        prepare_training_data(str(data), str(data_dir))
    else:
        data_dir = data.parent

    if not args.prepare_only:
        train_lora(args.model, str(data_dir), args.output,
                   args.iters, args.lora_rank, args.learning_rate, args.batch_size)


if __name__ == "__main__":
    main()
