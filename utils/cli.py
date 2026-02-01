"""CLI argument parsing and setup utilities."""
import sys
import argparse

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("⚠️  Warning: ollama not installed. Install with: pip install ollama")
    print("⚠️  Make sure Ollama is running: https://ollama.ai\n")
    sys.exit(1)

# Supported models for benchmarking
SUPPORTED_MODELS = ["phi3", "llama3", "gemma:2b"]


def parse_arguments():
    """Parse and return command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the SLM Efficiency Benchmark using Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Supported Models: {', '.join(SUPPORTED_MODELS)}

Examples:
  # Run benchmark on a single model
  python benchmark.py --model phi3

  # Run on all supported models
  python benchmark.py --model all

  # Custom settings
  python benchmark.py --model llama3 --max-tokens 200 --temperature 0.8

  # Custom analysis model
  python benchmark.py --model all --analysis-model deepseek-v3.1:671b-cloud

  # Custom dataset
  python benchmark.py --model gemma:2b --data-path data/custom_dataset.json

Prerequisites:
  1. Install Ollama: https://ollama.ai
  2. Pull models: ollama pull phi3 && ollama pull llama3 && ollama pull gemma:2b
  3. Start Ollama: ollama serve
        """
    )
    parser.add_argument("--model", type=str, default="phi3",
                        help=f"Model name or 'all' to test all models. Supported: {', '.join(SUPPORTED_MODELS)}")
    parser.add_argument("--max-tokens", type=int, default=100,
                        help="Max tokens to generate per inference")
    parser.add_argument("--temperature", type=float, default=0.7,
                        help="Sampling temperature")
    parser.add_argument("--data-path", type=str, default="data/sample_subset.json",
                        help="Path to benchmark dataset")
    parser.add_argument("--max-retries", type=int, default=2,
                        help="Max retries for failed inferences")
    parser.add_argument("--analysis-model", type=str, default="deepseek-v3.1:671b-cloud",
                        help="Model to use for LLM-based comparison analysis (default: deepseek-v3.1:671b-cloud)")
    parser.add_argument("--verbose", action="store_true",
                        help="Enable verbose logging")

    return parser.parse_args()


def verify_ollama_connection():
    """Verify Ollama is installed and running."""
    if not OLLAMA_AVAILABLE:
        print("❌ Ollama Python package not installed")
        print("   Install with: pip install ollama")
        sys.exit(1)

    try:
        ollama.list()
    except Exception as e:
        print(f"❌ Cannot connect to Ollama service: {e}")
        print("   💡 Make sure Ollama is running: ollama serve")
        sys.exit(1)


def determine_models_to_test(model_arg: str):
    """Determine which models to test based on CLI argument."""
    if model_arg.lower() == "all":
        models = SUPPORTED_MODELS
        print(f"🔬 Testing all {len(models)} models: {', '.join(models)}\n")
        return models
    else:
        return [model_arg]
