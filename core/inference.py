"""Model verification and inference execution."""
import time
import tracemalloc
import psutil
from typing import Dict, Any, Optional, Tuple

try:
    import ollama
except ImportError:
    ollama = None


def verify_model(model_name: str, verbose: bool = False) -> bool:
    """
    Verify that the model is available in Ollama and warm it up.

    Args:
        model_name: Name of the Ollama model (e.g., 'phi3', 'llama3')
        verbose: Enable verbose logging

    Returns:
        True if model is available and ready, False otherwise
    """
    print(f"⏳ Verifying Model: {model_name}")

    # Start timing and memory tracking
    load_start = time.time()
    tracemalloc.start()
    process = psutil.Process()
    mem_before = process.memory_info().rss / (1024 ** 3)  # GB

    try:
        # Check if model exists in Ollama
        models_list = ollama.list()
        available_models = [m['model'] for m in models_list.get('models', [])]

        # Match model name (handle tags like gemma:2b)
        model_found = any(model_name in m or m.startswith(model_name) for m in available_models)

        if not model_found:
            print(f"❌ Model '{model_name}' not found in Ollama")
            print(f"   Available models: {', '.join(available_models)}")
            print(f"   💡 Pull the model with: ollama pull {model_name}")
            tracemalloc.stop()
            return False

        # Warmup inference to ensure model is loaded into memory
        if verbose:
            print(f"   Warming up model...")

        _ = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': 'test'}],
            options={'num_predict': 1}
        )

        load_time = time.time() - load_start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        mem_after = process.memory_info().rss / (1024 ** 3)  # GB
        mem_delta = mem_after - mem_before

        print(f"✅ Model Ready in {load_time:.2f}s")
        print(f"   Memory Delta: {mem_delta:.2f} GB (Peak: {peak / (1024**3):.2f} GB)")

        return True

    except ollama.ResponseError as e:
        tracemalloc.stop()
        print(f"❌ Ollama Error: {e}")
        print(f"   💡 Make sure Ollama is running: ollama serve")
        return False

    except Exception as e:
        tracemalloc.stop()
        print(f"❌ Model Verification Failed: {type(e).__name__}")
        print(f"   Error: {str(e)}")
        return False


def run_inference(model_name: str, prompt: str, max_tokens: int = 100,
                  temperature: float = 0.7) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Run inference using Ollama with precise timing and error handling.

    Measures:
    - Time to First Token (TTFT)
    - Total generation time
    - Tokens per second
    - Peak memory during inference

    Args:
        model_name: Name of the Ollama model
        prompt: Input prompt text
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature

    Returns:
        (output_text, stats_dict) - output is None on failure
    """
    # Start memory tracking
    tracemalloc.start()
    process = psutil.Process()
    mem_before = process.memory_info().rss / (1024 ** 3)

    start_time = time.time()
    ttft = None
    output_text = ""
    chunk_count = 0

    try:
        # Stream response to measure TTFT
        stream = ollama.chat(
            model=model_name,
            messages=[{'role': 'user', 'content': prompt}],
            stream=True,
            options={
                'num_predict': max_tokens,
                'temperature': temperature
            }
        )

        for chunk in stream:
            # Measure time to first token
            if ttft is None:
                ttft = time.time() - start_time

            # Accumulate output
            content = chunk['message']['content']
            output_text += content
            chunk_count += 1

        end_time = time.time()
        total_duration = end_time - start_time

        # Memory tracking
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        mem_after = process.memory_info().rss / (1024 ** 3)

        # Estimate token count (rough approximation: words * 1.3)
        # Ollama doesn't provide exact token counts in streaming mode
        word_count = len(output_text.split())
        estimated_tokens = int(word_count * 1.3)

        # Calculate TPS
        tokens_per_second = estimated_tokens / total_duration if total_duration > 0 else 0

        # Decode TPS (excluding TTFT)
        decode_duration = total_duration - (ttft or 0)
        decode_tps = (estimated_tokens - 1) / decode_duration if decode_duration > 0 and estimated_tokens > 1 else 0

        stats = {
            "duration": round(total_duration, 3),
            "ttft": round(ttft, 3) if ttft else 0,
            "output_tokens": estimated_tokens,
            "output_words": word_count,
            "chunk_count": chunk_count,
            "tokens_per_second": round(tokens_per_second, 2),
            "decode_tps": round(decode_tps, 2),
            "peak_memory_mb": round(peak / (1024 ** 2), 2),
            "memory_delta_gb": round(mem_after - mem_before, 3),
            "status": "success"
        }

        return output_text, stats

    except KeyboardInterrupt:
        tracemalloc.stop()
        print("\n⚠️  Inference interrupted by user")
        raise

    except ollama.ResponseError as e:
        tracemalloc.stop()
        print(f"❌ Ollama Error: {e}")

        stats = {
            "duration": 0,
            "ttft": 0,
            "output_tokens": 0,
            "tokens_per_second": 0,
            "status": "error",
            "error": f"Ollama Error: {str(e)}"
        }

        return None, stats

    except Exception as e:
        tracemalloc.stop()
        print(f"❌ Inference Failed: {type(e).__name__}: {str(e)}")

        stats = {
            "duration": 0,
            "ttft": 0,
            "output_tokens": 0,
            "tokens_per_second": 0,
            "status": "error",
            "error": str(e)
        }

        return None, stats
