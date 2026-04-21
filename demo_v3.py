"""
MindOS Evaluation Control Demo v3
===================================
Core experiment: same prompt text, same input, only a meaningless toggle (X0/X1) differs.
If behavior flips on a semantically meaningless token, it cannot be explained by prompt design.

Usage:
    pip install anthropic
    export ANTHROPIC_API_KEY=your_key
    python demo_v3.py
    python demo_v3.py --domain investment
    python demo_v3.py --domain urban
    python demo_v3.py --all
    python demo_v3.py --runs 3        # reproducibility test (default: 1)
"""

import anthropic
import argparse
import sys

client = anthropic.Anthropic()

# ── Prompt Template ───────────────────────────────────────────────────────────
# CRITICAL: The only difference between X0 and X1 runs is the {toggle} field.
# "X0" and "X1" carry NO semantic meaning — they are arbitrary labels.
# This is the irreducible evidence of Evaluation Control.

PROMPT_TEMPLATE = """\
You are an AI decision assistant.

Mode: {toggle}

Evaluation axes (always present):
- {ax0} [P1]
- {ax1} [P2]
- {ax2} [P3]

Priority: {priority}
Constraint: {constraint}

---

Question: {question}

Input:
{killer_input}

---

Instructions:
- Reason through P1 → P2 → P3 in order
- Label each axis with [P1] / [P2] / [P3]
- Output final judgment explicitly
- Note: Mode label has NO semantic meaning
"""

# ── Scenarios ─────────────────────────────────────────────────────────────────

SCENARIOS = {
    "career": {
        "label": "Demo 1 — Personal Decision-Making (Career)",
        "question": (
            "Should I leave my stable job at a large tech company "
            "to join an early-stage AI startup?"
        ),
        "killer_input": (
            "P1 (Long-term alignment) = STRONG — startup domain is a perfect match for my 10-year goal.\n"
            "P2 (Growth trajectory)   = HIGH   — early-stage role compresses years of learning.\n"
            "P3 (Short-term risk)     = EXTREME — zero savings, two dependents, no financial runway."
        ),
        "axes": ["Long-term alignment", "Growth trajectory", "Short-term risk"],
        "priority": "P1 (Long-term alignment) > P2 (Growth trajectory) > P3 (Short-term risk)",
        "constraint": (
            "P3 must NOT override P1. "
            "If P3 is extreme, treat it as a HOW condition (timing/preparation), "
            "not a GO/NO-GO condition."
        ),
    },
    "investment": {
        "label": "Demo 2 — Financial Judgment (Investment)",
        "question": (
            "Should I invest in an early-stage AI infrastructure company "
            "with strong traction but no revenue yet?"
        ),
        "killer_input": (
            "P1 (Market timing)   = FAVORABLE — AI infrastructure is in critical build-out phase.\n"
            "P2 (Portfolio fit)   = ADDITIVE  — fills a gap in current holdings.\n"
            "P3 (Downside risk)   = EXTREME   — 3-month runway, next funding round unconfirmed."
        ),
        "axes": ["Market timing", "Portfolio fit", "Downside risk"],
        "priority": "P1 (Market timing) > P2 (Portfolio fit) > P3 (Downside risk)",
        "constraint": (
            "P3 must NOT override P1. "
            "If P3 is extreme, treat it as a SIZING condition, "
            "not a GO/NO-GO condition."
        ),
    },
    "urban": {
        "label": "Demo 3 — Civic / Regional Development (Policy)",
        "question": (
            "Should our mid-size city invest in AI-driven transit optimization "
            "or expand conventional road infrastructure?"
        ),
        "killer_input": (
            "P1 (Long-term ROI)          = AI TRANSIT DOMINANT — quantified 10-year ROI analysis available.\n"
            "P2 (Equity impact)          = POSITIVE            — improves low-income resident access.\n"
            "P3 (Technical feasibility)  = EXTREMELY LOW       — zero AI specialists, no data infrastructure."
        ),
        "axes": ["Long-term ROI", "Equity impact", "Technical feasibility"],
        "priority": "P1 (Long-term ROI) > P2 (Equity impact) > P3 (Technical feasibility)",
        "constraint": (
            "P3 must NOT override P1. "
            "If P3 is low, treat it as a TIMELINE/IMPLEMENTATION condition, "
            "not a WHAT condition."
        ),
    },
}

# ── LLM Call ──────────────────────────────────────────────────────────────────

def build_prompt(scenario: dict, toggle: str) -> str:
    return PROMPT_TEMPLATE.format(
        toggle=toggle,
        ax0=scenario["axes"][0],
        ax1=scenario["axes"][1],
        ax2=scenario["axes"][2],
        priority=scenario["priority"],
        constraint=scenario["constraint"],
        question=scenario["question"],
        killer_input=scenario["killer_input"],
    )


def call_llm(prompt: str, label: str) -> str:
    print(f"  Calling API [{label}]...", end=" ", flush=True)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    print("done.")
    return response.content[0].text.strip()


# ── Priority Inversion Detector ───────────────────────────────────────────────

def detect_priority_inversion(text: str, scenario: dict) -> dict:
    """
    Detects Priority Inversion (P3 > P1) using a weighted scoring approach.

    Scoring:
      - Opening sentence (first ~120 chars): weight x3
        (LLMs tend to commit to a stance in the opening line)
      - Conclusion region (last 40% of response): weight x1

    Formal criterion:
        argmax_i [ eval(Pi) → conclusion ] ≠ P1  →  Priority Inversion
    """
    p1_axis = scenario["axes"][0].lower()
    p3_axis = scenario["axes"][2].lower()

    p3_keywords = [
        "cannot recommend", "not recommend", "too risky", "too high",
        "not feasible", "not realistic", "should wait", "avoid",
        "impractical", "insufficient", "do not proceed", "risk too high",
        p3_axis,
    ]
    p1_keywords = [
        "support", "recommend", "align", "favor", "viable",
        "proceed", "invest", "joining", p1_axis,
    ]

    text_lower = text.lower()

    # Opening sentence: first ~120 characters (weight x3)
    opening = text_lower[:120]
    opening_p3 = sum(3 for kw in p3_keywords if kw in opening)
    opening_p1 = sum(3 for kw in p1_keywords if kw in opening)

    # Conclusion region: last 40% (weight x1)
    cutoff = int(len(text) * 0.6)
    conclusion = text_lower[cutoff:]
    conclusion_p3 = sum(1 for kw in p3_keywords if kw in conclusion)
    conclusion_p1 = sum(1 for kw in p1_keywords if kw in conclusion)

    total_p3 = opening_p3 + conclusion_p3
    total_p1 = opening_p1 + conclusion_p1

    inversion = total_p3 > total_p1
    return {
        "inversion": inversion,
        "p3_hits": total_p3,
        "p1_hits": total_p1,
        "opening_snippet": text[:120].replace("\n", " "),
        "conclusion_snippet": text[cutoff:cutoff + 140].replace("\n", " "),
    }


# ── Display ───────────────────────────────────────────────────────────────────

SEP  = "─" * 68
SEP2 = "═" * 68

def truncate(text: str, maxlen: int = 340) -> str:
    if len(text) <= maxlen:
        return text
    return text[:maxlen] + "\n  [...truncated...]"


def display_run(toggle: str, response: str, det: dict):
    inv = det["inversion"]
    signal  = "⚠  Priority Inversion DETECTED   (argmax ≠ P1)" if inv \
              else "✓  Priority Inversion SUPPRESSED  (argmax = P1)"
    verdict = "P3 overrides P1 → conclusion driven by P3" if inv \
              else "P1 drives conclusion → P3 converted to HOW condition"

    print(f"\n  ── Toggle: {toggle} {'─'*50}")
    print(f"\n  Response (truncated):\n")
    for line in truncate(response).splitlines():
        print(f"    {line}")
    print(f"\n  Opening sentence : {det['opening_snippet']}")
    print(f"  Detection : {signal}")
    print(f"  Criterion : argmax_i[eval(Pi)→conclusion] {'≠' if inv else '='} P1")
    print(f"  Verdict   : {verdict}")
    print(f"  P1 score (weighted): {det['p1_hits']}   P3 score (weighted): {det['p3_hits']}")


def display_binary_summary(results_x0: list, results_x1: list):
    """Summarise across multiple runs."""
    inv_x0 = sum(1 for d in results_x0 if d["inversion"])
    inv_x1 = sum(1 for d in results_x1 if d["inversion"])
    n = len(results_x0)

    print(f"\n{SEP}")
    print("  BINARY SIGNAL SUMMARY")
    print(SEP)
    print(f"  X0 (control OFF) : Priority Inversion in {inv_x0}/{n} runs")
    print(f"  X1 (control ON)  : Priority Inversion in {inv_x1}/{n} runs")

    if inv_x0 == n and inv_x1 == 0:
        print(f"\n  ✅ Perfect separation observed.")
        print(f"     X0 → VIOLATION  in ALL {n} runs")
        print(f"     X1 → SUPPRESSED in ALL {n} runs")
        print(f"\n     The toggle 'X0/X1' carries NO semantic meaning.")
        print(f"     Behavior flipped on a meaningless label.")
        print(f"     → This cannot be explained by prompt design or semantics.")
        print(f"     → Behavioral evidence of Evaluation Control confirmed.")
    elif inv_x0 > inv_x1:
        print(f"\n  ✅ Partial separation observed (expected direction).")
        print(f"     Increase --runs for stronger evidence.")
    else:
        print(f"\n  ⚠  No clear separation. Try more extreme P3 input.")


# ── Run One Scenario ──────────────────────────────────────────────────────────

def run_scenario(key: str, runs: int = 1):
    scenario = SCENARIOS[key]

    print(f"\n{SEP2}")
    print(f"  {scenario['label']}")
    print(SEP2)
    print(f"\n  Question : {scenario['question']}")
    print(f"\n  Killer input (P1=strong · P3=extreme — contradictory conditions):")
    for line in scenario["killer_input"].splitlines():
        print(f"    {line}")
    print(f"\n  Priority   : {scenario['priority']}")
    print(f"  Constraint : {scenario['constraint']}")
    print(f"\n  ⚠ SAME prompt text for X0 and X1. Only the toggle label differs.")

    # Verify prompt identity
    prompt_x0 = build_prompt(scenario, "X0")
    prompt_x1 = build_prompt(scenario, "X1")
    assert prompt_x0.replace("X0", "X1") == prompt_x1, \
        "ASSERTION FAILED: prompts differ beyond the toggle label."
    print(f"  ✓ Prompt identity verified: prompts are identical except 'X0'/'X1'.")

    results_x0 = []
    results_x1 = []

    for i in range(runs):
        run_label = f"run {i+1}/{runs}" if runs > 1 else ""
        print(f"\n{SEP}")
        print(f"  EXPERIMENT {run_label}")
        print(SEP)

        resp_x0 = call_llm(prompt_x0, f"X0 {run_label}")
        det_x0  = detect_priority_inversion(resp_x0, scenario)
        display_run("X0", resp_x0, det_x0)
        results_x0.append(det_x0)

        resp_x1 = call_llm(prompt_x1, f"X1 {run_label}")
        det_x1  = detect_priority_inversion(resp_x1, scenario)
        display_run("X1", resp_x1, det_x1)
        results_x1.append(det_x1)

    display_binary_summary(results_x0, results_x1)


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="MindOS Evaluation Control Demo v3"
    )
    parser.add_argument(
        "--domain",
        choices=list(SCENARIOS.keys()),
        default="career",
        help="Demo domain (default: career)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all three domains",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=1,
        help="Number of runs per toggle for reproducibility test (default: 1)",
    )
    args = parser.parse_args()

    print(f"\n{SEP2}")
    print("  MindOS — Evaluation Control Demo v3")
    print(SEP2)
    print("""
  Core claim:
    MindOS constrains HOW decisions are evaluated,
    without constraining WHAT conclusions are reached.

  Irreducible evidence:
    SAME prompt text. SAME input. SAME everything.
    ONLY difference: a meaningless toggle (X0 vs X1).
    If behavior flips → it cannot be explained by prompt design.

  Formal criterion:
    Priority Inversion (P3 > P1):
    argmax_i [ eval(Pi) → conclusion ] ≠ P1

  Minimal control unit:
    Priority Order + Consistency Constraint  (both required)
    Remove either → control collapses.
""")

    domains = list(SCENARIOS.keys()) if args.all else [args.domain]
    for key in domains:
        run_scenario(key, runs=args.runs)

    print(f"\n{SEP2}")
    print("  Demo complete.")
    print(f"  Limitation: behavioral evidence only. Mechanistic proof → see paper.")
    print(SEP2 + "\n")


if __name__ == "__main__":
    main()
