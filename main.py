#!/usr/bin/env python3
"""
SLM-Bench: The Efficiency Index for On-Device AI

Main entry point for running benchmarks on Small Language Models.
"""
import sys
import json
import time

from utils.cli import parse_arguments, verify_ollama_connection, determine_models_to_test
from core.io import load_data, save_results, print_model_summary
from core.runner import run_model_benchmark
from core.analysis import calculate_summary, generate_llm_comparison


def main():
    """Main entry point - orchestrates the benchmark workflow."""
    # Parse arguments
    args = parse_arguments()
    csv_file = "results/benchmark_log.csv"

    # Verify Ollama is running
    verify_ollama_connection()

    # Determine which models to test
    models_to_test = determine_models_to_test(args.model)

    # Load dataset
    try:
        data = load_data(args.data_path)
    except FileNotFoundError:
        print(f"❌ Dataset not found: {args.data_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in dataset: {e}")
        sys.exit(1)

    # Run benchmarks
    all_results = []
    model_summaries = []

    for model_name in models_to_test:
        results = run_model_benchmark(model_name, data, args)

        if results is None:  # Model verification failed
            continue

        # Calculate summary
        config = {
            "max_tokens": args.max_tokens,
            "temperature": args.temperature,
            "max_retries": args.max_retries
        }
        summary, failed_items = calculate_summary(model_name, results, config)

        # Save results
        json_file = save_results(model_name, results, summary, csv_file)

        # Print summary
        print_model_summary(model_name, summary, failed_items, json_file)

        # Collect for final analysis
        all_results.extend(results)
        model_summaries.append(summary)

    # Generate LLM comparison if multiple models tested
    if len(model_summaries) > 1:
        comparison_file = f"results/comparison_{int(time.time())}.json"
        generate_llm_comparison(model_summaries, comparison_file, args.analysis_model)
    else:
        comparison_file = None

    # Final summary
    print(f"\n{'='*60}")
    print(f"✅ All Benchmarks Complete!")
    print(f"{'='*60}")
    print(f"Models Tested:   {len(models_to_test)}")
    print(f"Total Runs:      {len(all_results)}")
    print(f"\n📊 Summary log:  {csv_file}")

    if comparison_file:
        print(f"🤖 Comparison:   {comparison_file}")


if __name__ == "__main__":
    main()
