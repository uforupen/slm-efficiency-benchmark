# ⚡ SLM-Bench: The Efficiency Index for On-Device AI

> **The "Consumer Reports" for Small Language Models**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Ollama](https://img.shields.io/badge/Ollama-Required-green.svg)](https://ollama.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🛑 The Problem

Standard AI benchmarks (MMLU, GSM8K, HumanEval) measure **Capability**:
- *"Can this model solve PhD-level physics problems?"*
- *"Can it pass the bar exam?"*
- Evaluated on unlimited cloud hardware with 80GB VRAM

**They completely ignore Feasibility for on-device AI:**
- *"Will this model drain my laptop battery in 20 minutes?"*
- *"Can it run on my MacBook without thermal throttling?"*
- *"Do I get 5 tokens/sec or 50 tokens/sec for everyday tasks?"*

## 💡 The Solution: Efficiency Index

**SLM-Bench** introduces a new standard for evaluating Small Language Models on **real consumer hardware**. We measure the **Cost of Intelligence** across three dimensions:

### 1. ⚡ Speed
- **Tokens Per Second (TPS)**: Actual throughput on your device
- **Time to First Token (TTFT)**: Responsiveness for interactive use
- **Decode Speed**: Sustained generation performance

### 2. 🏋️ Weight
- **Peak RAM Usage**: Maximum memory footprint during inference
- **Memory Delta**: How much RAM the model consumes
- **Resource Efficiency**: Can it run alongside your other apps?

### 3. 🎯 Utility
- **Goldilocks Dataset**: Everyday tasks (summarization, extraction, reasoning)
- **Not academic benchmarks**: Real-world prompts users actually care about
- **Category Breakdown**: Performance by task type

## 🚀 Quick Start

### Prerequisites

```bash
# 1. Install Ollama (https://ollama.ai)
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pull benchmark models
ollama pull phi3
ollama pull llama3
ollama pull gemma:2b

# 3. Start Ollama
ollama serve
```

### Installation

```bash
git clone https://github.com/uforupen/slm-efficiency-bench.git
cd slm-efficiency-bench
pip install -r requirements.txt
```

### Run Benchmark

```bash
# Test a single model
python benchmark.py --model phi3

# Test all models and generate comparison
python benchmark.py --model all

# Custom analysis model (for more insightful comparisons)
python benchmark.py --model all --analysis-model deepseek-v3.1:671b-cloud
```

## 📊 What You Get

### Per-Model JSON Reports
```json
{
  "summary": {
    "model": "phi3",
    "performance": {
      "avg_tokens_per_second": 22.50,
      "avg_ttft": 0.123,
      "avg_decode_tps": 23.15,
      "total_tokens_generated": 5420
    },
    "category_breakdown": {
      "Summarization": {"avg_tps": 24.1},
      "Extraction": {"avg_tps": 21.8}
    }
  },
  "results": [ /* detailed per-prompt results */ ]
}
```

### Cross-Model Comparison (LLM-Analyzed)
When testing multiple models, a separate LLM (default: DeepSeek v3) analyzes the results and provides:
- **Performance Ranking**: Which model is most efficient overall
- **Strengths & Weaknesses**: What each model excels at
- **Use Case Recommendations**: Best model for your specific needs
- **Key Insights**: Surprising patterns in the data

Analysis is provided in **dual format**:
- `readable`: Full markdown/text analysis (easy to read)
- `structured`: Parsed JSON fields (for programmatic access)

### CSV Time-Series Log
Track performance across runs:
```csv
timestamp,model,avg_tps,avg_ttft,avg_decode_tps,success_rate,total_items
1738425600,phi3,22.50,0.123,23.15,100.0%,100
1738425700,llama3,18.30,0.156,19.20,100.0%,100
```

## 🎯 Target Use Cases

**This benchmark is for:**
- 📱 Developers building on-device AI apps
- 💻 Researchers evaluating SLM efficiency
- 🔋 Engineers optimizing for battery life
- 🚀 Teams choosing models for edge deployment

**This benchmark is NOT for:**
- ❌ Measuring "AGI capabilities"
- ❌ Ranking models on academic problems
- ❌ Cloud-scale deployments with unlimited resources

## 😬 Hall of Shame

**Why Speed Without Quality Is Meaningless**

Fast but wrong answers are useless. Here are some memorable fails from our benchmarks:

### Example 1: The "Apple Energy" Incident
**Prompt**: *"What renewable energy source is named after a fruit?"*

**Phi-3 Response** (22.5 tok/s):
> "Apple Energy is a renewable energy company founded by Apple Inc. that focuses on solar power..."

**Reality**: There is no "Apple Energy." The answer is **solar** (from Latin *sol* = sun, not a fruit). This highlights why we need the **Utility** dimension alongside Speed and Weight.

### Example 2: Constraint Catastrophe
**Prompt**: *"Write a sentence about dogs without using the letter 'e'"*

**Model X Response** (18.3 tok/s):
> "The energetic puppy played fetch in the garden."

**Count**: Uses 'e' **seven times**. Fast, but completely failed the constraint.

### Example 3: The Confident Hallucination
**Prompt**: *"Extract the meeting time from this email: 'Let's catch up soon!'"*

**Model Y Response** (25.1 tok/s):
> "Meeting scheduled for 3:00 PM on Thursday."

**Reality**: No time was mentioned. The model hallucinated with confidence.

---

**The Point**: A model that generates gibberish at 50 tok/s is worse than one that's correct at 20 tok/s. The Efficiency Index measures **useful** throughput, not just raw speed.

> *"The best model isn't the fastest. It's the one that gives you correct answers at acceptable speed on your hardware."*

Got a great fail? [Submit it here](https://github.com/uforupen/slm-efficiency-bench/issues) and we'll add it to the Hall of Shame!

## 📈 Roadmap

- [x] Core benchmarking framework with Ollama integration
- [x] Modular, testable architecture
- [x] LLM-based cross-model analysis
- [ ] Expand dataset to 100 "Goldilocks" prompts
- [ ] Add energy consumption metrics (battery drain)
- [ ] Visualization dashboard (Speed vs Accuracy plots)
- [ ] Public leaderboard
- [ ] Technical report publication

## 🤝 Contributing

We're building the **Efficiency Index** standard for on-device AI. Contributions welcome!

**Priority areas:**
1. **Dataset Expansion**: Adding realistic, everyday prompts (see `data/sample_subset.json`)
2. **New Metrics**: Energy usage, thermal throttling, sustained performance
3. **Visualization**: Plots comparing Speed vs Utility
4. **Model Coverage**: Testing more SLMs as they're released

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with:
- [Ollama](https://ollama.ai) - Local LLM runtime
- Community SLMs: Phi-3 (Microsoft), Llama 3 (Meta), Gemma (Google)

## 📞 Contact

Questions or suggestions? [Open an issue](https://github.com/uforupen/slm-efficiency-bench/issues) on GitHub!

---

**Remember:** The best model isn't the one that scores highest on MMLU. It's the one that runs efficiently on *your* hardware for *your* tasks.
