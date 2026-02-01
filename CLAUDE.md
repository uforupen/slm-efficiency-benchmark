# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

SLM-Bench (Small Language Model Benchmark) is a benchmarking framework focused on **efficiency metrics** for on-device AI using **Ollama**. Unlike traditional benchmarks that measure capability (MMLU, GSM8K), this evaluates models on three practical axes:
1. **Speed**: Tokens per second (TPS) on consumer hardware
2. **Weight**: Peak RAM usage during inference
3. **Utility**: Accuracy on practical tasks (Summarization, Extraction, Instruction Following)

The goal is to answer questions like "Does this model drain my battery?" and "Is 4-bit quantization actually usable?" rather than "Can it solve PhD-level problems?"

**Supported Models**: phi3, llama3, gemma:2b

## Development Commands

### Prerequisites
```bash
# 1. Install Ollama (https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Start Ollama service
ollama serve

# 3. Pull benchmark models
ollama pull phi3
ollama pull llama3
ollama pull gemma:2b
```

### Setup
```bash
pip install -r requirements.txt
```

### Running Benchmarks
```bash
# Run benchmark on a single model
python benchmark.py --model phi3

# Run on all supported models
python benchmark.py --model all

# Custom settings
python benchmark.py --model llama3 --max-tokens 200 --temperature 0.8

# Use different analysis model for comparison (more capable reasoning)
python benchmark.py --model all --analysis-model deepseek-v3.1:671b-cloud

# Custom dataset
python benchmark.py --model gemma:2b --data-path data/custom_dataset.json

# With retry logic
python benchmark.py --model phi3 --max-retries 3
```

### Viewing Results
```bash
# Detailed results (JSON)
cat results/run_<model>_<timestamp>.json

# Summary log (CSV)
cat results/benchmark_log.csv

# Watch live results
tail -f results/benchmark_log.csv
```

## Architecture

### Code Organization (Modular Architecture)

The codebase is organized into focused modules (789 total lines, down from 653 in single file):

```
benchmark.py              # Main entry point (87 lines)
├── utils/
│   └── cli.py           # CLI & setup (88 lines)
│       ├── parse_arguments()
│       ├── verify_ollama_connection()
│       └── determine_models_to_test()
└── core/
    ├── inference.py      # Model operations (201 lines)
    │   ├── verify_model()
    │   └── run_inference()
    ├── runner.py         # Benchmark execution (110 lines)
    │   ├── run_single_item()
    │   └── run_model_benchmark()
    ├── analysis.py       # Statistics & LLM analysis (208 lines)
    │   ├── calculate_summary()
    │   └── generate_llm_comparison()
    └── io.py            # Data loading & saving (95 lines)
        ├── load_data()
        ├── save_results()
        └── print_model_summary()
```

**Key Design Principles:**
- **Procedural, not OOP**: Functions, not classes (appropriate for batch jobs)
- **Single Responsibility**: Each module has one clear purpose
- **Easy Testing**: Import and test individual functions
- **Minimal main()**: Just orchestrates, no business logic (87 lines vs 278 before)
- **Clear Dependencies**: Module imports show call hierarchy

### Production Implementation Overview
The codebase implements production-grade benchmarking using **Ollama** with robust error handling, precise measurement systems, and multi-model testing.

### Systems Engineering Features

**Ollama Integration**
- Uses Ollama's Python API for model inference (handles GPU/CPU automatically)
- Supports streaming responses for TTFT measurement
- Model verification with warmup inference before benchmarking
- Automatic model availability checking via `ollama.list()`
- Multi-model testing with `--model all` flag

**Error Handling & Recovery**
- Connection verification to Ollama service at startup
- Model availability checking before benchmark runs
- Comprehensive exception handling for Ollama errors (`ollama.ResponseError`)
- Retry logic with configurable attempts (`--max-retries`)
- Diagnostic messages suggesting fixes (pull model, start Ollama service)
- Failed items tracked separately without halting entire benchmark
- Graceful handling of keyboard interrupts

**Precise Timing & Measurement (benchmark.py:run_inference)**
- **Time-to-First-Token (TTFT)**: Measured by streaming chunks and recording first chunk latency
- **Decode TPS**: Calculated excluding TTFT to isolate decode performance
- **Memory Tracking**: Uses both `tracemalloc` (Python heap) and `psutil` (RSS) for comprehensive memory profiling
- **Timer Isolation**: Model verification time explicitly separated from inference time
- **Peak Memory**: Tracks maximum memory usage during each operation
- **Token Estimation**: Since Ollama streaming doesn't provide exact token counts, estimates using word count × 1.3

**Resource Management**
- Memory tracking properly started/stopped with `tracemalloc`
- Process-level memory monitoring via `psutil`
- Memory deltas calculated (before/after) for accurate measurement
- Keyboard interrupt handling for clean exits
- Per-model result isolation when testing multiple models

**Critical Timing Implementations**

Model Verification (benchmark.py:verify_model):
```python
# Timer starts BEFORE verification
load_start = time.time()

# Check model exists in Ollama
models_list = ollama.list()

# CRITICAL: Warmup inference ensures model is loaded into memory
_ = ollama.chat(model=model_name, messages=[...], options={'num_predict': 1})

# Timer stops AFTER warmup completes
load_time = time.time() - load_start
```
This ensures the model is downloaded, loaded into memory (VRAM/RAM), and inference-ready before benchmarking starts.

Inference Streaming (benchmark.py:run_inference):
```python
stream = ollama.chat(model=model_name, messages=[...], stream=True, options={...})

for chunk in stream:
    if ttft is None:
        ttft = time.time() - start_time  # First chunk received
    output_text += chunk['message']['content']
    chunk_count += 1
```
Streaming allows TTFT measurement and progressive text accumulation for accurate performance metrics.

Retry Logic (benchmark.py:run_single_item):
```python
for attempt in range(max_retries + 1):
    try:
        output, stats = run_inference(model_name, prompt, ...)
        if stats['status'] == 'success':
            break  # Success, exit retry loop
        elif attempt < max_retries:
            print(f"   Retrying ({attempt + 1}/{max_retries})...")
    except KeyboardInterrupt:
        sys.exit(0)  # User interrupt, halt immediately
    except Exception as e:
        if attempt < max_retries:
            time.sleep(1)  # Brief delay before retry
```
Failed items are tracked but don't halt the entire benchmark run.

### Workflow: Single Model Benchmark

```
main()
  ↓
  parse_arguments()                    # Get CLI args
  verify_ollama_connection()           # Check Ollama running
  determine_models_to_test()           # ["phi3"] or all 3 models
  load_data()                          # Load benchmark prompts
  ↓
  for each model:
    run_model_benchmark()
      ↓
      verify_model()                   # Warmup, check availability
      ↓
      for each item:
        run_single_item()
          ↓
          run_inference()              # Streaming + TTFT measurement
            (with retries)
      ↓
      calculate_summary()              # Aggregate stats (min/max/avg)
      save_results()                   # JSON + CSV
      print_model_summary()            # Console output
  ↓
  generate_llm_comparison()            # If multiple models tested
```

**Data Format**

Input data structure (data/sample_subset.json):
- `id`: Test case identifier
- `category`: Task type (Summarization, Extraction, Instruction Following)
- `prompt`: Input text for the model

Output format (results/run_<timestamp>_<model>.json):
```json
{
  "summary": {
    "model": "phi3",
    "timestamp": 1738425600,
    "config": {
      "max_tokens": 100,
      "temperature": 0.7,
      "max_retries": 2
    },
    "total_items": 2,
    "successful": 2,
    "failed": 0,
    "success_rate": 1.0,
    "performance": {
      "avg_tokens_per_second": 22.00,
      "min_tokens_per_second": 18.50,
      "max_tokens_per_second": 25.50,
      "avg_ttft": 0.123,
      "min_ttft": 0.110,
      "max_ttft": 0.135,
      "avg_decode_tps": 23.15,
      "avg_duration": 2.456,
      "avg_output_tokens": 54.0,
      "total_tokens_generated": 108,
      "total_time_spent": 4.91
    },
    "category_breakdown": {
      "Summarization": {
        "count": 1,
        "avg_tps": 22.00
      },
      "Extraction": {
        "count": 1,
        "avg_tps": 22.00
      }
    }
  },
  "results": [
    {
      "id": "test_01",
      "model": "phi3",
      "prompt": "...",
      "output": "...",
      "category": "Summarization",
      "metrics": {
        "duration": 2.456,
        "ttft": 0.123,
        "output_tokens": 54,
        "output_words": 42,
        "chunk_count": 38,
        "tokens_per_second": 22.00,
        "decode_tps": 23.15,
        "peak_memory_mb": 2847.33,
        "memory_delta_gb": 0.012,
        "status": "success"
      }
    }
  ]
}
```
Note: `output_tokens` is estimated as `output_words × 1.3` since Ollama streaming doesn't provide exact token counts.

CSV summary log (results/benchmark_log.csv):
- Append-only log tracking all benchmark runs
- Columns: timestamp, model, avg_tps, avg_ttft, avg_decode_tps, success_rate, total_items
- Used for cross-run and cross-model comparisons

LLM Comparison Analysis (results/comparison_<timestamp>.json):
- Auto-generated when testing multiple models with `--model all`
- Uses separate analysis model (default: deepseek-v3.1:671b-cloud) for unbiased insights
- Dual format for both human and programmatic consumption
- Structure:
  ```json
  {
    "meta": {
      "timestamp": 1738425600,
      "models_compared": ["phi3", "llama3", "gemma:2b"],
      "analysis_model": "deepseek-v3.1:671b-cloud"
    },
    "summaries": [...],
    "analysis": {
      "readable": "Full markdown/text analysis for humans to read...",
      "structured": {
        "ranking": "...",
        "strengths_weaknesses": "...",
        "recommendations": "...",
        "insights": "...",
        "winner": "..."
      }
    }
  }
  ```

  **Note**: `analysis.readable` always contains the full LLM response as readable text. `analysis.structured` contains parsed JSON (if available) for programmatic access, or `null` if parsing failed.

### Analysis Pipeline

**Built-in LLM Analysis (benchmark.py:generate_llm_comparison)**
- Automatically triggered when benchmarking multiple models (`--model all`)
- Uses one of the tested models to generate comparative analysis
- Analyzes performance data and provides:
  - Model rankings based on efficiency metrics
  - Strengths and weaknesses for each model
  - Use case recommendations (which model for which scenario)
  - Key insights and surprising findings
  - Overall winner declaration with rationale
- Output saved to `results/comparison_<timestamp>.json`
- Falls back to raw summary data if LLM analysis fails

**Manual Analysis**
The `analysis/` directory is intended for post-processing scripts and notebooks that generate "Speed vs. Accuracy" visualizations from the benchmark results JSON files. Currently empty.

## Key Dependencies
- **Ollama**: Local LLM runtime (binary installation from ollama.ai)
- `ollama>=0.1.0`: Python client for Ollama API
- `psutil>=5.9.0`: Process and system memory monitoring
- `pandas>=2.0.0`, `matplotlib>=3.7.0`: Results analysis and visualization
- `tqdm>=4.66.0`: Progress tracking (reserved for future use)

## Code Modification Guidelines

**When adding new models:**
1. Update `SUPPORTED_MODELS` list at top of benchmark.py
2. Pull model locally: `ollama pull <model_name>`
3. No other code changes needed (auto-handled by loop)

**When adding new metrics:**
1. Update `run_inference()` to capture the metric
2. Update `calculate_summary()` to aggregate it (add to performance dict)
3. Update `print_model_summary()` to display it
4. Update JSON schema documentation in this file

**When modifying retry logic:**
- Only edit `run_single_item()` function
- Don't touch main loop or individual inference calls

**When changing output format:**
- Modify `save_results()` for JSON structure
- Modify CSV header/row in `save_results()` for CSV changes
- Update data format examples in this CLAUDE.md

## Common Issues & Solutions

**"Cannot connect to Ollama service"**
- Start Ollama: `ollama serve`
- Check if Ollama is running: `ps aux | grep ollama`
- Verify installation: `ollama --version`

**"Model 'phi3' not found in Ollama"**
- Pull the model: `ollama pull phi3`
- List available models: `ollama list`
- Check model name spelling (case-sensitive)

**"TTFT is 0 or suspiciously low"**
- Check if Ollama streaming is working properly
- Verify model completed warmup in verify_model()
- Try with `--verbose` flag for detailed logging

**"tokens_per_second much lower than expected"**
- Check system resources: `htop` or Activity Monitor
- Verify Ollama has GPU access (if available)
- Ensure no other heavy processes are running
- Try smaller model (gemma:2b) to isolate hardware vs model size issues

**"Output tokens seem inaccurate"**
- Token counts are estimated (words × 1.3) since Ollama streaming doesn't provide exact counts
- For precise token counting, consider using the non-streaming API (loses TTFT measurement)
- Actual token counts may vary by ~10-20% from estimates
