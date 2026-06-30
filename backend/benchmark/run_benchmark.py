"""
AFAC2026 Benchmark 评测脚本
评测维度：响应时延、合规通过率、数据真实率、信号产出率
"""
import asyncio
import json
import time
import statistics
from pathlib import Path
from datetime import datetime

# 30只A股样本（覆盖主板/创业板/科创板）
SAMPLE_STOCKS = [
    "600519", "000858", "002594", "601318", "600036",
    "300750", "688981", "600900", "000001", "601012",
    "600276", "002415", "300059", "601888", "000333",
    "600887", "002304", "601166", "300124", "688111",
    "600030", "000725", "601398", "300014", "002475",
    "600050", "601857", "000651", "688599", "601288",
]

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "benchmark_results.json"


async def run_benchmark(max_stocks: int = 30, quick: bool = True):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    from agents.orchestrator import orchestrator
    from services.compliance_service import compliance_service

    stocks = SAMPLE_STOCKS[:max_stocks]
    latencies = []
    compliance_pass = 0
    compliance_total = 0
    real_data_count = 0
    signal_count = 0
    errors = []
    per_stock = []

    print(f"开始 Benchmark: {len(stocks)} 只股票")
    print("-" * 50)

    for i, symbol in enumerate(stocks, 1):
        t0 = time.time()
        try:
            result = await orchestrator.analyze_stock(
                symbol=symbol,
                analysis_type="quick" if quick else "comprehensive",
                include_news=not quick,
                include_risk=True,
                include_strategy=False,
            )
            elapsed = time.time() - t0
            latencies.append(elapsed)

            if result.get("status") == "error":
                errors.append({"symbol": symbol, "error": result.get("error")})
                continue

            signal_count += 1
            source = result.get("data_source", "unknown")
            if source not in ("mock", "error"):
                real_data_count += 1

            # 合规检查
            compliance_total += 1
            check = await compliance_service.check(symbol, action="buy")
            if check.get("passed"):
                compliance_pass += 1

            per_stock.append({
                "symbol": symbol,
                "latency_s": round(elapsed, 2),
                "signal": result.get("recommendation", {}).get("signal", "hold"),
                "confidence": result.get("recommendation", {}).get("confidence", 0),
                "data_source": source,
                "compliance_passed": check.get("passed", False),
            })
            print(f"  [{i}/{len(stocks)}] {symbol} OK {elapsed:.1f}s signal={per_stock[-1]['signal']}")
        except Exception as e:
            errors.append({"symbol": symbol, "error": str(e)})
            print(f"  [{i}/{len(stocks)}] {symbol} FAIL: {e}")

    latencies.sort()
    n = len(latencies) or 1
    summary = {
        "run_at": datetime.now().isoformat(),
        "sample_size": len(stocks),
        "success_count": signal_count,
        "error_count": len(errors),
        "latency": {
            "p50_s": round(statistics.median(latencies), 2) if latencies else 0,
            "p95_s": round(latencies[int(n * 0.95)] if latencies else 0, 2),
            "mean_s": round(statistics.mean(latencies), 2) if latencies else 0,
            "max_s": round(max(latencies), 2) if latencies else 0,
        },
        "compliance_pass_rate_percent": round(compliance_pass / compliance_total * 100, 1) if compliance_total else 0,
        "real_data_rate_percent": round(real_data_count / signal_count * 100, 1) if signal_count else 0,
        "signal_success_rate_percent": round(signal_count / len(stocks) * 100, 1),
        "mode": "quick" if quick else "comprehensive",
        "per_stock": per_stock,
        "errors": errors,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("-" * 50)
    print(f"P50 时延: {summary['latency']['p50_s']}s")
    print(f"P95 时延: {summary['latency']['p95_s']}s")
    print(f"合规通过率: {summary['compliance_pass_rate_percent']}%")
    print(f"真实数据率: {summary['real_data_rate_percent']}%")
    print(f"结果已保存: {OUTPUT_PATH}")
    return summary


if __name__ == "__main__":
    asyncio.run(run_benchmark())
