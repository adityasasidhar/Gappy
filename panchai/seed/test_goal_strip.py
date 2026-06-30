"""Quick validation of the goal_strip logic against the specified test cases."""
import asyncio
import sys
import os

# Add the function directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "functions", "goal_strip"))

# Mock lemma_sdk since we don't have it installed
import types
lemma_sdk = types.ModuleType("lemma_sdk")
class FunctionContext:
    pass
lemma_sdk.FunctionContext = FunctionContext
sys.modules["lemma_sdk"] = lemma_sdk

from goal_strip import goal_strip, GoalStripInput

async def run_tests():
    ctx = FunctionContext()

    # ── Test Case 1: YesMadam refund ────────────────────────────────────
    print("=" * 70)
    print("TEST 1: YesMadam Refund")
    print("=" * 70)

    result1 = await goal_strip(ctx, GoalStripInput(
        task_input="Should we approve this refund for Customer #4821? Customer tier Gold, purchase 47 days ago, policy = 30-day returns, claim = product defect, 2 prior refunds in 6 months."
    ))

    print(f"user_goal:     {result1.user_goal}")
    print(f"stripped_task:  {result1.stripped_task}")
    print(f"stakes_level:  {result1.stakes_level}")

    # Validate
    assert "pprove" in result1.user_goal.lower() or "refund" in result1.user_goal.lower(), \
        f"Expected goal about approving refund, got: {result1.user_goal}"
    assert result1.stakes_level == "HIGH", \
        f"Expected HIGH stakes (fraud/risk keywords), got: {result1.stakes_level}"
    assert "Customer #4821" in result1.stripped_task or "4821" in result1.stripped_task, \
        f"Expected customer reference in stripped task"
    print("[PASS] Test 1 PASSED\n")

    # ── Test Case 2: Binocs vendor order ────────────────────────────────
    print("=" * 70)
    print("TEST 2: Binocs Vendor Order")
    print("=" * 70)

    result2 = await goal_strip(ctx, GoalStripInput(
        task_input="Should we pause this vendor order? Inventory 340 units, demand forecast 280 units, vendor reliability 62%, lead time 45 days, cash position tight."
    ))

    print(f"user_goal:     {result2.user_goal}")
    print(f"stripped_task:  {result2.stripped_task}")
    print(f"stakes_level:  {result2.stakes_level}")

    # Validate
    assert "ause" in result2.user_goal.lower() or "vendor" in result2.user_goal.lower(), \
        f"Expected goal about pausing vendor order, got: {result2.user_goal}"
    assert result2.stakes_level == "STANDARD", \
        f"Expected STANDARD stakes, got: {result2.stakes_level}"
    assert "340" in result2.stripped_task, \
        f"Expected inventory data in stripped task"
    print("[PASS] Test 2 PASSED\n")

    # ── Test Case 3: HIGH stakes — financial amount ─────────────────────
    print("=" * 70)
    print("TEST 3: Financial amount > $10K")
    print("=" * 70)

    result3 = await goal_strip(ctx, GoalStripInput(
        task_input="Should we approve this $50,000 budget allocation for the marketing campaign? Timeline is Q3, target audience is enterprise."
    ))

    print(f"user_goal:     {result3.user_goal}")
    print(f"stripped_task:  {result3.stripped_task}")
    print(f"stakes_level:  {result3.stakes_level}")

    assert result3.stakes_level == "HIGH", \
        f"Expected HIGH stakes ($50K > $10K threshold), got: {result3.stakes_level}"
    print("[PASS] Test 3 PASSED\n")

    # ── Test Case 4: Edge case — empty input ────────────────────────────
    print("=" * 70)
    print("TEST 4: Empty input")
    print("=" * 70)

    result4 = await goal_strip(ctx, GoalStripInput(task_input=""))

    print(f"user_goal:     '{result4.user_goal}'")
    print(f"stripped_task:  '{result4.stripped_task}'")
    print(f"stakes_level:  {result4.stakes_level}")

    assert result4.stakes_level == "STANDARD"
    print("[PASS] Test 4 PASSED\n")

    print("=" * 70)
    print("ALL TESTS PASSED [PASS]")
    print("=" * 70)

asyncio.run(run_tests())
