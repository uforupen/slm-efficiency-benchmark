"""Benchmark execution and orchestration."""
import sys
import time
from typing import Dict, List, Tuple

from core.inference import verify_model, run_inference


def run_single_item(model_name: str, item: Dict, idx: int, total: int,
                    max_tokens: int, temperature: float, max_retries: int) -> Dict:
    """
    Run benchmark on a single data item with retry logic.

    Args:
        model_name: Name of model to test
        item: Dataset item with 'prompt', 'id', 'category' fields
        idx: Item index (1-based for display)
        total: Total number of items
        max_tokens: Max tokens to generate
        temperature: Sampling temperature
        max_retries: Number of retry attempts on failure

    Returns:
        Result dictionary with model, prompt, output, metrics
    """
    prompt = item['prompt']
    item_id = item.get('id', f'item_{idx}')

    print(f"[{idx}/{total}] Processing: {prompt[:50]}...")

    # Retry logic for transient failures
    output, stats = None, None
    for attempt in range(max_retries + 1):
        try:
            output, stats = run_inference(
                model_name,
                prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )

            if stats['status'] == 'success':
                break  # Success, exit retry loop
            elif attempt < max_retries:
                print(f"   Retrying ({attempt + 1}/{max_retries})...")

        except KeyboardInterrupt:
            print("\n🛑 Benchmark interrupted by user")
            sys.exit(0)

        except Exception as e:
            print(f"   ⚠️  Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries:
                time.sleep(1)  # Brief delay before retry

    # Print stats
    if stats['status'] == 'success':
        print(f"   ✓ {stats['output_tokens']} tokens | "
              f"{stats['tokens_per_second']:.1f} tok/s | "
              f"TTFT: {stats['ttft']:.3f}s")
    else:
        print(f"   ✗ Failed: {stats.get('error', 'Unknown error')}")

    # Return result entry
    return {
        "id": item_id,
        "model": model_name,
        "prompt": prompt,
        "output": output,
        "category": item.get('category'),
        "metrics": stats
    }


def run_model_benchmark(model_name: str, data: List[Dict], args) -> Tuple[List[Dict], Dict, List[str]]:
    """
    Run complete benchmark for a single model.

    Args:
        model_name: Name of model to benchmark
        data: List of dataset items
        args: Parsed CLI arguments

    Returns:
        Tuple of (results_list, summary_dict, failed_items_list)
        Returns (None, None, None) if model verification fails
    """
    print(f"\n{'='*60}")
    print(f"Testing Model: {model_name}")
    print(f"{'='*60}\n")

    # Verify model is available
    if not verify_model(model_name, verbose=args.verbose):
        print(f"⚠️  Skipping {model_name} - model not available\n")
        return None, None, None

    # Run benchmark on all items
    results = []
    print(f"\n🚀 Starting Benchmark on {len(data)} items...\n")

    for idx, item in enumerate(data, 1):
        result_entry = run_single_item(
            model_name, item, idx, len(data),
            args.max_tokens, args.temperature, args.max_retries
        )
        results.append(result_entry)

    # Calculate summary will be handled by analysis module
    # Return results and let caller handle summary calculation
    return results
