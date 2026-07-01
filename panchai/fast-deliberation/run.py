import asyncio, argparse, json, sys
from pipeline import run_pipeline, TASK_EXAMPLES


async def main():
    parser = argparse.ArgumentParser(description="PANCHAI Fast Deliberation Pipeline")
    parser.add_argument("--task", help="Task description")
    parser.add_argument("--goal", default="", help="User's desired outcome")
    parser.add_argument("--context", default="", help="Additional context")
    parser.add_argument("--example", choices=list(TASK_EXAMPLES.keys()), help="Run a built-in example")
    parser.add_argument("--benchmark", type=int, default=0, help="Run N iterations and report stats")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    if args.benchmark > 0:
        ex = TASK_EXAMPLES.get(args.example or "yesmadam")
        times = []
        for i in range(args.benchmark):
            if args.json:
                print(json.dumps({"iteration": i+1}))
            r = await run_pipeline(task=ex["task"], goal=ex["goal"], context=ex["context"])
            times.append(r["elapsed"])
            if not args.json:
                print(f"  Run {i+1}: {r['elapsed']}s | verdict={r['verdict']['verdict']} conf={r['verdict']['confidence_score']}")

        avg = sum(times) / len(times)
        best = min(times)
        worst = max(times)
        if not args.json:
            print(f"\nBenchmark ({args.benchmark} runs):")
            print(f"  Avg: {avg:.2f}s  Best: {best:.2f}s  Worst: {worst:.2f}s")
        else:
            print(json.dumps({"avg": round(avg, 2), "best": best, "worst": worst, "runs": times}))
        return

    if args.example:
        ex = TASK_EXAMPLES[args.example]
        result = await run_pipeline(task=ex["task"], goal=ex["goal"], context=ex["context"])
    elif args.task:
        result = await run_pipeline(task=args.task, goal=args.goal, context=args.context)
    else:
        print("Provide --task or --example. Use --help for options.")
        sys.exit(1)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"\nPipeline complete in {result['elapsed']}s")
        print(f"Verdict: {result['verdict']['verdict']} (confidence: {result['verdict']['confidence_score']})")
        print(f"Consensus: {result['verdict']['consensus_met']}  HITL needed: {result['verdict']['hitl_required']}")
        print(f"\nCouncil votes:")
        votes = result["verdict"]["vote_breakdown"]
        print(f"  FOR: {votes.get('FOR', 0)}  AGAINST: {votes.get('AGAINST', 0)}  ABSTAIN: {votes.get('ABSTAIN', 0)}")
        print(f"\nResponses:")
        for c in result["council_responses"]:
            print(f"  [{c['agent_id']}] {c['position']} ({c['confidence']}): {c['argument']}")


if __name__ == "__main__":
    asyncio.run(main())
