"""Analysis and summary calculation."""
import time
import json
from typing import Dict, List, Tuple

try:
    import ollama
except ImportError:
    ollama = None


def calculate_summary(model_name: str, results: List[Dict], config: Dict) -> Tuple[Dict, List[str]]:
    """
    Calculate comprehensive summary statistics for a model's results.

    Args:
        model_name: Name of the model
        results: List of result dictionaries
        config: Configuration dict with max_tokens, temperature, etc.

    Returns:
        Tuple of (summary_dict, failed_items_list)
    """
    successful = [r for r in results if r['metrics']['status'] == 'success']
    failed_items = [r['id'] for r in results if r['metrics']['status'] != 'success']

    summary = {
        "model": model_name,
        "timestamp": int(time.time()),
        "config": config,
        "total_items": len(results),
        "successful": len(successful),
        "failed": len(failed_items),
        "success_rate": len(successful) / len(results) if results else 0
    }

    if successful:
        # Performance metrics
        tps_values = [r['metrics']['tokens_per_second'] for r in successful]
        ttft_values = [r['metrics']['ttft'] for r in successful]
        decode_tps_values = [r['metrics']['decode_tps'] for r in successful]
        duration_values = [r['metrics']['duration'] for r in successful]
        token_values = [r['metrics']['output_tokens'] for r in successful]

        summary["performance"] = {
            "avg_tokens_per_second": round(sum(tps_values) / len(tps_values), 2),
            "min_tokens_per_second": round(min(tps_values), 2),
            "max_tokens_per_second": round(max(tps_values), 2),
            "avg_ttft": round(sum(ttft_values) / len(ttft_values), 3),
            "min_ttft": round(min(ttft_values), 3),
            "max_ttft": round(max(ttft_values), 3),
            "avg_decode_tps": round(sum(decode_tps_values) / len(decode_tps_values), 2),
            "avg_duration": round(sum(duration_values) / len(duration_values), 3),
            "avg_output_tokens": round(sum(token_values) / len(token_values), 1),
            "total_tokens_generated": sum(token_values),
            "total_time_spent": round(sum(duration_values), 2)
        }

        # Category breakdown
        category_stats = {}
        for result in successful:
            cat = result.get('category', 'Unknown')
            if cat not in category_stats:
                category_stats[cat] = {
                    'count': 0,
                    'avg_tps': 0,
                    'tps_values': []
                }
            category_stats[cat]['count'] += 1
            category_stats[cat]['tps_values'].append(result['metrics']['tokens_per_second'])

        for cat in category_stats:
            tps_vals = category_stats[cat]['tps_values']
            category_stats[cat]['avg_tps'] = round(sum(tps_vals) / len(tps_vals), 2)
            del category_stats[cat]['tps_values']  # Remove raw values from output

        summary["category_breakdown"] = category_stats

    return summary, failed_items


def generate_llm_comparison(model_summaries: List[Dict], output_path: str,
                           analysis_model: str = "deepseek-v3.1:671b-cloud"):
    """
    Generate LLM-based comparison and analysis of benchmark results.

    Args:
        model_summaries: List of summary dictionaries from each model run
        output_path: Path to save the analysis JSON
        analysis_model: Model to use for analysis (separate from benchmarked models)
    """
    if not model_summaries:
        return

    print(f"\n{'='*60}")
    print(f"🤖 Generating LLM-based Analysis using {analysis_model}")
    print(f"{'='*60}\n")

    # Determine which model to use for analysis
    actual_analysis_model = analysis_model

    try:
        # Prepare data for LLM analysis
        analysis_prompt = """You are an AI performance analyst. Analyze the following benchmark results and provide insights.

Benchmark Data:
"""
        for summary in model_summaries:
            analysis_prompt += f"\n{json.dumps(summary, indent=2)}\n"

        analysis_prompt += """
Please provide:
1. Performance Ranking: Rank models by overall efficiency (consider TPS, TTFT, and consistency)
2. Strengths & Weaknesses: For each model, identify what it does best and worst
3. Use Case Recommendations: Which model is best for which scenario?
4. Key Insights: Any notable patterns or surprising findings
5. Winner: Overall best model and why

Format your response as structured JSON with these keys: ranking, strengths_weaknesses, recommendations, insights, winner
"""

        print(f"   Using analysis model: {actual_analysis_model}")

        # Try to use specified analysis model
        try:
            response = ollama.chat(
                model=actual_analysis_model,
                messages=[{'role': 'user', 'content': analysis_prompt}],
                options={'temperature': 0.3}  # Lower temperature for more focused analysis
            )
        except ollama.ResponseError as e:
            # Fallback to first benchmarked model
            print(f"   ⚠️  Analysis model '{actual_analysis_model}' failed: {e}")
            actual_analysis_model = model_summaries[0]['model']
            print(f"   Falling back to: {actual_analysis_model}")

            response = ollama.chat(
                model=actual_analysis_model,
                messages=[{'role': 'user', 'content': analysis_prompt}],
                options={'temperature': 0.3}
            )

        analysis_text = response['message']['content']

        # Always save readable version for human consumption
        readable_analysis = analysis_text

        # Try to extract structured JSON from response
        analysis_json = None
        try:
            # Look for JSON block in markdown code fence
            if "```json" in analysis_text:
                json_start = analysis_text.find("```json") + 7
                json_end = analysis_text.find("```", json_start)
                analysis_json = json.loads(analysis_text[json_start:json_end].strip())
            elif "```" in analysis_text:
                json_start = analysis_text.find("```") + 3
                json_end = analysis_text.find("```", json_start)
                analysis_json = json.loads(analysis_text[json_start:json_end].strip())
            else:
                # Try parsing the whole response as JSON
                analysis_json = json.loads(analysis_text)
        except json.JSONDecodeError:
            # JSON parsing failed, but we have readable text
            analysis_json = None

        # Create comprehensive analysis output
        comparison_output = {
            "meta": {
                "timestamp": int(time.time()),
                "models_compared": [s['model'] for s in model_summaries],
                "analysis_model": actual_analysis_model
            },
            "summaries": model_summaries,
            "analysis": {
                "readable": readable_analysis,  # Human-readable markdown/text
                "structured": analysis_json     # Parsed JSON (null if parsing failed)
            }
        }

        # Save analysis
        with open(output_path, 'w') as f:
            json.dump(comparison_output, f, indent=2)

        print(f"✅ Analysis saved: {output_path}\n")

        # Print quick summary
        if analysis_json and isinstance(analysis_json, dict):
            if "ranking" in analysis_json:
                print("📊 Quick Insights:")
                print(f"   Ranking: {analysis_json.get('ranking', 'N/A')}")
                if "winner" in analysis_json:
                    print(f"   Winner: {analysis_json['winner']}")
        else:
            print("📊 Analysis generated (see 'readable' field in comparison file)")

    except Exception as e:
        print(f"⚠️  Analysis generation failed: {e}")
        print(f"   Saving raw summaries instead...")

        # Fallback: save raw summaries
        fallback_output = {
            "meta": {
                "timestamp": int(time.time()),
                "models_compared": [s['model'] for s in model_summaries],
                "analysis_model_attempted": analysis_model,
                "error": str(e),
                "note": "LLM analysis failed, raw summaries only"
            },
            "summaries": model_summaries,
            "analysis": {
                "readable": "Analysis generation failed. See meta.error for details.",
                "structured": None
            }
        }

        with open(output_path, 'w') as f:
            json.dump(fallback_output, f, indent=2)

        print(f"📁 Raw summaries saved: {output_path}")
