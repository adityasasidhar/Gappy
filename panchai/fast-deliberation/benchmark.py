import asyncio, json
from pipeline import run_pipeline, TASK_EXAMPLES


async def run_benchmark(iterations: int = 10):
    print(f"Running {iterations} iterations per example...\n")

    for name, ex in TASK_EXAMPLES.items():
        print(f"=== {name} ===")
        times = []
        for i in range(iterations):
            r = await run_pipeline(task=ex["task"], goal=ex["goal"], context=ex["context"])
            times.append(r["elapsed"])

        avg = sum(times) / len(times)
        best = min(times)
        worst = max(times)
        print(f"  Avg: {avg:.2f}s  Best: {best:.2f}s  Worst: {worst:.2f}s")
        print(f"  Times: {[f'{t:.2f}' for t in times]}")
        print()

    print("All benchmarks complete.")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
