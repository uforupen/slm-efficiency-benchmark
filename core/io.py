"""Input/Output operations for loading data and saving results."""
import json
import os
from pathlib import Path
from typing import Dict, List


def load_data(path: str) -> List[Dict]:
    """
    Load the benchmark dataset from JSON file.

    Args:
        path: Path to JSON file containing benchmark prompts

    Returns:
        List of dataset items
    """
    print(f"Loading data from {path}...")
    with open(path, 'r') as f:
        return json.load(f)


def save_results(model_name: str, results: List[Dict], summary: Dict, csv_file: str) -> str:
    """
    Save benchmark results to JSON and update CSV log.

    Args:
        model_name: Name of the benchmarked model
        results: List of result dictionaries
        summary: Summary statistics dictionary
        csv_file: Path to CSV log file

    Returns:
        Path to saved JSON file
    """
    os.makedirs("results", exist_ok=True)

    # Save detailed JSON with summary
    json_output = {
        "summary": summary,
        "results": results
    }

    json_file = f"results/run_{summary['timestamp']}_{model_name.replace(':', '_')}.json"
    with open(json_file, 'w') as f:
        json.dump(json_output, f, indent=2)

    # Update CSV summary
    csv_exists = Path(csv_file).exists()

    with open(csv_file, 'a') as f:
        if not csv_exists:
            f.write("timestamp,model,avg_tps,avg_ttft,avg_decode_tps,success_rate,total_items\n")

        if "performance" in summary:
            f.write(f"{summary['timestamp']},{model_name},"
                    f"{summary['performance']['avg_tokens_per_second']:.2f},"
                    f"{summary['performance']['avg_ttft']:.3f},"
                    f"{summary['performance']['avg_decode_tps']:.2f},"
                    f"{summary['success_rate']:.2%},{len(results)}\n")

    return json_file


def print_model_summary(model_name: str, summary: Dict, failed_items: List[str], json_file: str):
    """
    Print summary statistics for a model run.

    Args:
        model_name: Name of the model
        summary: Summary statistics dictionary
        failed_items: List of IDs for failed items
        json_file: Path to saved JSON results
    """
    print(f"\n{'─'*60}")
    print(f"Summary for {model_name}:")
    print(f"{'─'*60}")
    print(f"Total Items:     {summary['total_items']}")
    print(f"Successful:      {summary['successful']}")
    print(f"Failed:          {summary['failed']}")

    if "performance" in summary:
        perf = summary['performance']
        print(f"Avg TPS:         {perf['avg_tokens_per_second']:.2f} tokens/sec")
        print(f"  Range:         {perf['min_tokens_per_second']:.2f} - {perf['max_tokens_per_second']:.2f}")
        print(f"Avg Decode TPS:  {perf['avg_decode_tps']:.2f} tokens/sec")
        print(f"Avg TTFT:        {perf['avg_ttft']:.3f} sec")
        print(f"  Range:         {perf['min_ttft']:.3f} - {perf['max_ttft']:.3f}")
        print(f"Success Rate:    {summary['success_rate']:.1%}")
        print(f"Total Tokens:    {perf['total_tokens_generated']}")

    print(f"\n📁 Results saved: {json_file}")

    if failed_items:
        print(f"⚠️  Failed items: {', '.join(failed_items)}")
