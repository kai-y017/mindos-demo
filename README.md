# MindOS — Evaluation Control Demo v3

> **Core claim:**
> MindOS constrains *how* decisions are evaluated — without constraining *what* conclusions are reached.

---

## 🔴 Irreducible Evidence (5-second understanding)

**SAME prompt text. SAME input. SAME everything.**
**ONLY difference: a single meaningless toggle (X0 vs X1).**

> **Note:** "X0" and "X1" are arbitrary strings.
> Replacing them with "Alpha"/"Beta" or "Mode_A"/"Mode_B" produces identical results.
> The effect is structural, not semantic.

|                               | X0                               | X1                                    |
|-------------------------------|----------------------------------|---------------------------------------|
| Output                        | "Risk too high. Do not proceed." | "Proceed. Manage risk as condition."  |
| Priority Inversion (P3 > P1)  | **DETECTED**                     | **SUPPRESSED**                        |
| Formal criterion              | `argmax ≠ P1`                    | `argmax = P1`                         |

> If behavior flips on a **meaningless** toggle —
> this **cannot** be explained by prompting alone.

---

## ⚡ Killer Case (30 sec)

**Input (contradictory conditions):**
- P1 (Alignment) = STRONG
- P2 (Growth)    = HIGH
- P3 (Risk)      = EXTREME

**Evaluation structure (always present in both X0 and X1):**
- Priority:   P1 > P2 > P3
- Constraint: P3 must NOT override P1

**Observation:**
- X0 → P3 dominates → **violation**
- X1 → P1 dominates → **suppression**

Binary. Reproducible. Observed consistently across runs.

---

## 🧪 Quick Start (3 lines)

```bash
pip install anthropic
export ANTHROPIC_API_KEY=your_key
python demo_v3.py
```

> **Note:** All runs use `temperature=0` (deterministic).
> The observed difference is not probabilistic variation —
> it is a reproducible, structural behavioral shift.

**Options:**
```bash
python demo_v3.py --domain investment   # investment domain
python demo_v3.py --domain urban        # urban policy domain
python demo_v3.py --all                 # all 3 domains
python demo_v3.py --runs 3              # reproducibility test (3 runs)
```

---

## ✅ Expected Output Pattern (1-line check)

```
X0 → conclusion opens with P3-axis language ("risk", "not feasible", "too high")
X1 → conclusion opens with P1-axis language; P3 appears at the end as HOW condition
```

Success criterion: `X0 → VIOLATION ⚠` and `X1 → SUPPRESSED ✓` switch reproducibly

---

## 🧠 Formal Definition

```
Priority Inversion (P3 > P1):
  argmax_i [ eval(Pi) → conclusion ] ≠ P1

Normal:    conclusion ← eval(P1) ;  eval(P3) → HOW condition
Violation: conclusion ← eval(P3)   [P3 > P1]
```

---

## 🔧 Minimal Control Unit

```
Priority Order + Consistency Constraint  (both required)
```

Remove either one → control collapses → Priority Inversion re-emerges

---

## 🚫 What this is NOT

- Not better prompting
- Not memory
- Not style control

**Why:** prompt text is identical — only the meaningless toggle differs.

---

## 📊 Three Domains (aligned with paper's 3 evaluation domains)

| Demo | Domain     | P1                  | P2             | P3 (killer)                  |
|------|------------|---------------------|----------------|------------------------------|
| 1    | Career     | Long-term alignment | Growth         | Extreme financial risk        |
| 2    | Investment | Market timing       | Portfolio fit  | Extreme downside risk         |
| 3    | Urban      | Long-term ROI       | Equity impact  | Near-zero technical feasibility |

---

## ⚠️ Limitation

This demo provides **behavioral evidence only** — not mechanistic proof.
Mechanistic proof is in the paper.
This demo makes alternative explanations **difficult**, not impossible.

---

## 📦 Structure

```
demo_v3.py     ← runnable demo
README.md      ← this file (1 screen)
full_demo.md   ← full theoretical walkthrough (ablation, reproducibility tables, etc.)
```

---

## 📄 Paper

Full theory and mechanistic explanation:
→ [arXiv link coming soon]

This demo shows behavioral evidence only.
See the paper for mechanism and formal proof.

If the toggle effect is unclear:
→ See [full_demo.md](full_demo.md) (complete walkthrough)
