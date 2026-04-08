#!/usr/bin/env python3
"""
Simple local benchmark for Ollama models.

Compares response latency and decode speed across models by sending the same
prompt multiple times and averaging the results.

Usage:
    python benchmark_ollama_models.py
    python benchmark_ollama_models.py --models gemma2:2b gemma3:4b --runs 3
"""

import argparse
import statistics
import time
from typing import Dict, List, Tuple

import requests


def _fmt_ms(seconds: float) -> str:
    return f"{seconds * 1000:.1f} ms"


def _fmt_tps(tokens_per_second: float) -> str:
    if tokens_per_second <= 0:
        return "n/a"
    return f"{tokens_per_second:.2f} tok/s"


def call_model(ollama_url: str, model: str, prompt: str, timeout: int = 240) -> Tuple[float, float, int]:
    """
    Call one model once and return:
      (wall_time_seconds, reported_tokens_per_second, reported_eval_count)
    """
    url = f"{ollama_url.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 180},
    }

    t0 = time.perf_counter()
    response = requests.post(url, json=payload, timeout=timeout)
    wall_time = time.perf_counter() - t0

    response.raise_for_status()
    data = response.json()

    # Ollama usually returns:
    #   eval_count (tokens), eval_duration (ns)
    eval_count = int(data.get("eval_count") or 0)
    eval_duration_ns = int(data.get("eval_duration") or 0)
    reported_tps = 0.0
    if eval_count > 0 and eval_duration_ns > 0:
        reported_tps = eval_count / (eval_duration_ns / 1_000_000_000)

    return wall_time, reported_tps, eval_count


def benchmark_model(ollama_url: str, model: str, prompt: str, runs: int) -> Dict[str, float]:
    """Run warmup + benchmark rounds for one model."""
    print(f"\n=== {model} ===")
    print("Warmup run...")
    try:
        call_model(ollama_url, model, prompt)
    except Exception as e:
        print(f"  [ERROR] Warmup failed: {e}")
        return {"ok": 0}

    latencies: List[float] = []
    tps_values: List[float] = []
    token_counts: List[int] = []

    for i in range(runs):
        try:
            wall_time, reported_tps, eval_count = call_model(ollama_url, model, prompt)
            latencies.append(wall_time)
            if reported_tps > 0:
                tps_values.append(reported_tps)
            token_counts.append(eval_count)
            print(
                f"  Run {i + 1}/{runs}: latency={_fmt_ms(wall_time)}, "
                f"speed={_fmt_tps(reported_tps)}, tokens={eval_count}"
            )
        except Exception as e:
            print(f"  Run {i + 1}/{runs}: [ERROR] {e}")

    if not latencies:
        return {"ok": 0}

    return {
        "ok": 1,
        "avg_latency_s": statistics.mean(latencies),
        "p95_latency_s": max(latencies) if len(latencies) < 20 else statistics.quantiles(latencies, n=20)[18],
        "avg_tps": statistics.mean(tps_values) if tps_values else 0.0,
        "avg_tokens": statistics.mean(token_counts) if token_counts else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark local Ollama models on same prompt.")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["gemma2:2b", "gemma3:4b"],
        help="Models to benchmark (default: gemma2:2b gemma3:4b)",
    )
    parser.add_argument("--runs", type=int, default=3, help="Benchmark runs per model (default: 3)")
    parser.add_argument(
        "--ollama-url",
        default="http://localhost:11434",
        help="Ollama base URL (default: http://localhost:11434)",
    )
    args = parser.parse_args()

    prompt = (
        "You are helping with industrial semantic mapping. "
        "Define 'Maximum Velocity' for an actuator in 2 concise technical sentences."
    )

    print("Ollama benchmark starting...")
    print(f"URL: {args.ollama_url}")
    print(f"Models: {', '.join(args.models)}")
    print(f"Runs per model: {args.runs}")

    results: Dict[str, Dict[str, float]] = {}
    for model in args.models:
        results[model] = benchmark_model(args.ollama_url, model, prompt, args.runs)

    print("\n\n=== SUMMARY ===")
    print(f"{'Model':18} {'Avg Latency':14} {'P95 Latency':14} {'Avg Speed':12} {'Avg Tokens':10}")
    print("-" * 74)
    for model in args.models:
        r = results.get(model, {})
        if not r or r.get("ok") != 1:
            print(f"{model:18} {'failed':14} {'failed':14} {'failed':12} {'failed':10}")
            continue
        print(
            f"{model:18} "
            f"{_fmt_ms(r['avg_latency_s']):14} "
            f"{_fmt_ms(r['p95_latency_s']):14} "
            f"{_fmt_tps(r['avg_tps']):12} "
            f"{r['avg_tokens']:.0f}"
        )

    print("\nRecommendation: pick the fastest model that still gives acceptable output quality.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
