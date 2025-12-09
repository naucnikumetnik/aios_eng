#!/usr/bin/env python
import argparse
from dataclasses import dataclass
from typing import List, Optional, Dict

import pandas as pd
from datasets import load_dataset


# -------------------------
# Config / heuristics
# -------------------------

TASK_TO_METRIC_CANDIDATES: Dict[str, List[str]] = {
    # "preferred first, fallbacks after"
    "general": ["Average ⬆️", "Average"],
    "reasoning": ["MMLU-PRO", "MMLU PRO", "MMLU"],
    "math": ["MATH Lvl 5", "MATH"],
    # coding: we still use a general metric but narrow to code-y models
    "coding": ["Average ⬆️", "Average"],
}

CODE_MODEL_KEYWORDS = [
    "code", "coder", "codellama", "starcoder", "phind",
    "deepseek-coder", "qwen2.5-coder", "replit", "magicoder",
]

# rough VRAM per billion params (includes some overhead)
PRECISION_FACTORS = {
    "q4": 0.6,    # 4-bit quant
    "q8": 1.2,    # 8-bit quant
    "fp16": 2.3,  # 16-bit weights
}


@dataclass
class HardwareConfig:
    gpu_vram_gb: float
    cpu_ram_gb: float
    precision: str
    max_vram_frac: float = 0.9  # use at most this fraction of VRAM

    def max_model_params_b(self, moe: bool = False) -> float:
        """Return upper bound on params (in billions) we can comfortably fit."""
        factor = PRECISION_FACTORS[self.precision]
        effective_vram = self.gpu_vram_gb * self.max_vram_frac
        # crude MoE discount: only ~1/4 experts active
        moe_discount = 0.25 if moe else 1.0
        return (effective_vram / factor) / moe_discount


# -------------------------
# Core logic
# -------------------------

def load_leaderboard_df() -> pd.DataFrame:
    """
    Load Open LLM Leaderboard v2 'contents' dataset as a pandas DataFrame.

    Dataset has columns like:
    - 'Model' (hf repo id)
    - '#Params (B)'
    - 'Average ⬆️'
    - 'MATH Lvl 5', 'MMLU-PRO', etc.
    - 'Available on the hub', 'Official Providers', 'Type', 'MoE', ...
    """
    ds = load_dataset("open-llm-leaderboard/contents", split="train")
    df = ds.to_pandas()
    return df


def pick_metric_column(df: pd.DataFrame, task_type: str) -> str:
    candidates = TASK_TO_METRIC_CANDIDATES.get(task_type)
    if not candidates:
        raise ValueError(f"Unknown task_type '{task_type}'")

    for name in candidates:
        if name in df.columns:
            return name

    raise ValueError(
        f"None of the expected metric columns for task '{task_type}' found. "
        f"Tried: {candidates}. Available columns: {list(df.columns)}"
    )


def estimate_vram_gb(params_b: float, precision: str, moe: bool) -> float:
    factor = PRECISION_FACTORS[precision]
    moe_discount = 0.25 if moe else 1.0
    return params_b * factor * moe_discount


def filter_by_hardware(df: pd.DataFrame, hw: HardwareConfig) -> pd.DataFrame:
    # Keep only rows with a valid param count
    df = df.copy()
    if "#Params (B)" not in df.columns:
        raise ValueError("Leaderboard table has no '#Params (B)' column")

    df = df[df["#Params (B)"].notna()]
    df["#Params (B)"] = df["#Params (B)"].astype(float)

    # MoE flag might be missing; treat missing as False
    moe_col = "MoE"
    if moe_col in df.columns:
        moe_flags = df[moe_col].fillna(False).astype(bool)
    else:
        moe_flags = pd.Series([False] * len(df), index=df.index)

    df["est_vram_gb"] = [
        estimate_vram_gb(params_b, hw.precision, bool(moe))
        for params_b, moe in zip(df["#Params (B)"], moe_flags)
    ]

    vram_limit = hw.gpu_vram_gb * hw.max_vram_frac
    df = df[df["est_vram_gb"] <= vram_limit]

    return df


def base_filters(df: pd.DataFrame, chat_only: bool) -> pd.DataFrame:
    df = df.copy()

    # Drop pure provider endpoints, keep hub models
    if "Available on the hub" in df.columns:
        df = df[df["Available on the hub"] == True]
    if "Official Providers" in df.columns:
        df = df[df["Official Providers"] == False]
    if "Flagged" in df.columns:
        df = df[df["Flagged"] == False]

    if chat_only and "Type" in df.columns:
        mask = df["Type"].astype(str).str.contains("chat", case=False, na=False)
        df = df[mask]

    return df


def filter_for_task_type(df: pd.DataFrame, task_type: str) -> pd.DataFrame:
    df = df.copy()

    if task_type == "coding":
        if "Model" not in df.columns:
            return df  # nothing to do
        pattern = "|".join(CODE_MODEL_KEYWORDS)
        mask = df["Model"].astype(str).str.contains(pattern, case=False, na=False)
        df = df[mask]

    return df


def rank_models(
    df: pd.DataFrame,
    task_type: str,
    hw: HardwareConfig,
    chat_only: bool,
    top_k: int,
) -> pd.DataFrame:
    df = base_filters(df, chat_only=chat_only)
    df = filter_for_task_type(df, task_type=task_type)
    df = filter_by_hardware(df, hw)

    metric_col = pick_metric_column(df, task_type)
    df = df[df[metric_col].notna()]

    df = df.sort_values(metric_col, ascending=False)

    keep_cols = [
        "Model",
        "#Params (B)",
        metric_col,
        "Average ⬆️" if "Average ⬆️" in df.columns else None,
        "Type" if "Type" in df.columns else None,
        "Precision" if "Precision" in df.columns else None,
        "Architecture" if "Architecture" in df.columns else None,
        "est_vram_gb",
    ]
    keep_cols = [c for c in keep_cols if c is not None and c in df.columns]

    return df[keep_cols].head(top_k)


# -------------------------
# CLI
# -------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Pick HF leaderboard models filtered by your hardware."
    )
    p.add_argument(
        "--task-type",
        choices=list(TASK_TO_METRIC_CANDIDATES.keys()),
        default="general",
        help="Rough usage category: general, reasoning, math, coding.",
    )
    p.add_argument(
        "--gpu-vram-gb",
        type=float,
        default=16.0,
        help="Total GPU VRAM in GB (e.g. 16 for your RTX 5080).",
    )
    p.add_argument(
        "--cpu-ram-gb",
        type=float,
        default=128.0,
        help="System RAM in GB (currently not heavily used, but kept for future offload logic).",
    )
    p.add_argument(
        "--precision",
        choices=sorted(PRECISION_FACTORS.keys()),
        default="q4",
        help="Planned weight precision / quantization when you run the model locally.",
    )
    p.add_argument(
        "--max-vram-frac",
        type=float,
        default=0.9,
        help="Use at most this fraction of your GPU VRAM for model weights.",
    )
    p.add_argument(
        "--top-k",
        type=int,
        default=20,
        help="How many models to show.",
    )
    p.add_argument(
        "--no-chat-only",
        action="store_true",
        help="If set, do NOT restrict to chat/instruct models.",
    )
    return p.parse_args()


def main():
    args = parse_args()

    hw = HardwareConfig(
        gpu_vram_gb=args.gpu_vram_gb,
        cpu_ram_gb=args.cpu_ram_gb,
        precision=args.precision,
        max_vram_frac=args.max_vram_frac,
    )

    print(f"Loading Open LLM Leaderboard table...")
    df = load_leaderboard_df()

    chat_only = not args.no_chat_only

    ranked = rank_models(
        df=df,
        task_type=args.task_type,
        hw=hw,
        chat_only=chat_only,
        top_k=args.top_k,
    )

    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 160)
    print()
    print(f"Top {len(ranked)} models for task='{args.task_type}' "
          f"under ~{hw.gpu_vram_gb}GB VRAM ({hw.precision}, "
          f"≤{hw.max_vram_frac*100:.0f}% of VRAM):")
    print(ranked.to_string(index=False))


if __name__ == "__main__":
    main()
