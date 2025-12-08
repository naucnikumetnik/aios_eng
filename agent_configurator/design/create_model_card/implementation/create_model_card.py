#!/usr/bin/env python3
"""
Generate a structured "model card" JSON document for a GGUF LLM.

Usage:
    python gguf_model_card.py --model path/to/model.gguf [--out model_card.json]

Requires:
    pip install llama-cpp-python
"""

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import llama_cpp  # low-level API (C bindings + Llama class)
from llama_cpp import Llama


def _iso_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def build_model_card(llm: Llama, model_path: str) -> Dict[str, Any]:
    """
    Build a structured model card from a loaded Llama (GGUF) model.
    Tries to preserve all essential spec from metadata while giving a clean top-level card.
    """
    # Basic file info
    abs_path = os.path.abspath(model_path)
    file_size = os.path.getsize(model_path)
    mtime = datetime.utcfromtimestamp(os.path.getmtime(model_path)).replace(microsecond=0).isoformat() + "Z"

    # GGUF metadata from llama.cpp (scalar-only, no giant token arrays)
    metadata: Dict[str, Any] = getattr(llm, "metadata", {}) or {}

    # General / identity info
    model_id = os.path.splitext(os.path.basename(model_path))[0]
    general_name = metadata.get("general.name")
    general_arch = metadata.get("general.architecture")
    general_org = metadata.get("general.organization")
    general_desc = metadata.get("general.description")
    general_license = metadata.get("general.license")
    general_version = metadata.get("general.version")

    # Architecture-specific prefix (llama, phi2, qwen2, deepseek, etc.)
    arch_prefix = f"{general_arch}." if isinstance(general_arch, str) else ""
    ap = arch_prefix  # shorthand

    def md(key: str, default: Any = None) -> Any:
        return metadata.get(key, default)

    # Architecture / training-time hyperparameters (from GGUF)
    arch_meta = {
        "architecture": general_arch,
        "context_length_train": md(ap + "context_length"),
        "embedding_length": md(ap + "embedding_length"),
        "block_count": md(ap + "block_count"),
        "feed_forward_length": md(ap + "feed_forward_length"),
        "rope": {
            "dimension_count": md(ap + "rope.dimension_count"),
            "freq_base": md(ap + "rope.freq_base"),
        },
        "attention": {
            "head_count": md(ap + "attention.head_count"),
            "head_count_kv": md(ap + "attention.head_count_kv"),
            "layer_norm_rms_epsilon": md(ap + "attention.layer_norm_rms_epsilon"),
        },
        "quantization": {
            "file_type_raw": md("general.file_type"),
            "quantization_version": md("general.quantization_version"),
        },
    }

    # Runtime view from llama.cpp
    try:
        n_ctx_runtime = llm.n_ctx()
    except Exception:
        n_ctx_runtime = None

    try:
        n_vocab = llm.n_vocab()
    except Exception:
        n_vocab = None

    try:
        n_embd = llm.n_embd()
    except Exception:
        n_embd = None

    # Parameter count via low-level API (best effort)
    try:
        n_params = int(llama_cpp.llama_model_n_params(llm.model))  # type: ignore[attr-defined]
    except Exception:
        n_params = None

    # Tokenizer info (without tokens themselves; those aren't “card” material)
    tokenizer_info = {
        "model": md("tokenizer.ggml.model"),
        "bos_token_id": md("tokenizer.ggml.bos_token_id"),
        "eos_token_id": md("tokenizer.ggml.eos_token_id"),
        "unknown_token_id": md("tokenizer.ggml.unknown_token_id"),
        "padding_token_id": md("tokenizer.ggml.padding_token_id"),
        "add_bos_token": md("tokenizer.ggml.add_bos_token"),
        "add_eos_token": md("tokenizer.ggml.add_eos_token"),
        # Chat template name is in metadata, but the actual template is huge; keep reference only:
        "has_chat_template": "tokenizer.chat_template" in metadata,
    }

    # Identity block (person-card analogue)
    identity = {
        "entity_type": "model",
        "model_id": model_id,
        "display_name": general_name or model_id,
        "provider": general_org,
        "version": general_version,
        "short_description": general_desc,
        "architecture": general_arch,
        "parameter_count": n_params,
    }

    # Capabilities block: only what we can infer mechanically
    # You’ll fill richer stuff (task performance, evals) by hand later.
    capabilities = {
        "modalities": ["text"],  # GGUF + llama.cpp here is text LLM
        "primary_intended_uses": metadata.get("model.intended_uses"),
        "discouraged_uses": metadata.get("model.discouraged_uses"),
        "known_limits": metadata.get("model.known_limitations"),
        "context_window_tokens": {
            "train_context_tokens": arch_meta["context_length_train"],
            "runtime_context_tokens": n_ctx_runtime,
        },
    }

    # Experience / data profile – extremely thin because GGUF doesn’t encode training data sources.
    experience_or_data = {
        "training_data_summary": metadata.get("model.training_data.summary"),
        "training_data_cutoff": metadata.get("model.training_data.cutoff"),
        "data_safety_notes": metadata.get("model.data_safety_notes"),
    }

    # Availability / operational profile
    availability_or_operational_profile = {
        "runtime": {
            "vocab_size": n_vocab,
            "embedding_size": n_embd,
            "context_window_tokens_runtime": n_ctx_runtime,
        },
        "architecture": arch_meta,
        "tokenizer": tokenizer_info,
        "deployment_notes": metadata.get("model.deployment_notes"),
    }

    # Credentials / provenance
    credentials_or_provenance = {
        "source_file": {
            "path": abs_path,
            "size_bytes": file_size,
            "last_modified_utc": mtime,
        },
        "origin": {
            "original_repo": metadata.get("model.repo_url") or metadata.get("general.source_url"),
            "converted_from": metadata.get("model.converted_from"),
            "conversion_tool": metadata.get("model.conversion_tool"),
        },
        "license": general_license,
        "copyright": metadata.get("general.copyright"),
    }

    # Governance / risk – again, GGUF has almost nothing here; leave hooks for you to fill.
    governance = {
        "owner": general_org,
        "steward": metadata.get("model.steward"),
        "policy_references": metadata.get("model.policy_references"),
        "risk_notes": metadata.get("model.risk_notes"),
        "update_channel": metadata.get("model.update_channel"),
    }

    # Low-level: keep *all* llama.cpp + GGUF spec bits so nothing is lost.
    low_level = {
        "gguf_metadata": metadata,
        "llama_cpp_runtime": {
            "n_ctx_runtime": n_ctx_runtime,
            "n_vocab_runtime": n_vocab,
            "n_embd_runtime": n_embd,
            "n_params_runtime": n_params,
        },
    }

    card: Dict[str, Any] = {
        "schema_version": "0.1.0",
        "generated_at_utc": _iso_now(),
        "identity": identity,
        "capabilities": capabilities,
        "experience_or_data": experience_or_data,
        "availability_or_operational_profile": availability_or_operational_profile,
        "credentials_or_provenance": credentials_or_provenance,
        "governance": governance,
        "low_level": low_level,
    }

    return card


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a structured model-card JSON from a GGUF model.")
    parser.add_argument(
        "--model",
        required=True,
        help="Path to GGUF model file",
    )
    parser.add_argument(
        "--out",
        help="Output JSON path (default: <model>.model_card.json)",
    )
    parser.add_argument(
        "--ctx",
        type=int,
        default=512,  # safe, small, and matches llama-cpp default
        help="Context length used to init Llama. For metadata-only load, 512 is plenty.",
    )
    parser.add_argument(
        "--gpu-layers",
        type=int,
        default=0,
        help="Number of layers to offload to GPU when loading the model (default: 0). "
             "For metadata only, this usually doesn't matter.",
    )

    args = parser.parse_args(argv)

    model_path = args.model
    if not os.path.exists(model_path):
        print(f"ERROR: model file does not exist: {model_path}", file=sys.stderr)
        return 1

    out_path = args.out or (model_path + ".model_card.json")

    # Load GGUF model in vocab-only mode to avoid loading full weights
    try:
        effective_ctx = args.ctx if args.ctx and args.ctx > 0 else 512

        llm = Llama(
            model_path=model_path,
            vocab_only=True,          # only vocab + metadata, no weights
            n_ctx=effective_ctx,      # never 0, avoids buggy code paths
            n_gpu_layers=args.gpu_layers,  # fine as-is
            embedding=False,
            logits_all=False,
            verbose=False,
)

    except Exception as e:
        print(f"ERROR: failed to load model with llama_cpp.Llama: {e}", file=sys.stderr)
        return 1

    try:
        card = build_model_card(llm, model_path)
    finally:
        # Be nice and free resources explicitly
        try:
            llm.close()
        except Exception:
            pass

    # Dump JSON (pretty, but still deterministic)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(card, f, ensure_ascii=False, indent=2, sort_keys=False)

    print(f"Model card written to: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
