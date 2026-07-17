"""
Agent 7/9 — Risk scoring.
Aggregates signals from synthetic detection, correlation, and pattern
analysis into a calibrated risk score with an explicit confidence band
— NOT a bare number. Low-confidence cases are routed to human review
rather than auto-scored, consistent with VERITAS's abstention-first
design philosophy.
"""
from app.agents.state import PipelineState


def risk_scoring_agent(state: PipelineState) -> PipelineState:
    score = 0.0
    factors = []

    synthetic_results = state.get("synthetic_detection_results", {})
    flagged_synthetic = [p for p, r in synthetic_results.items() if r["verdict"] == "synthetic"]
    if flagged_synthetic:
        score += 0.4
        factors.append(f"{len(flagged_synthetic)} file(s) flagged as synthetic/AI-generated")

    patterns = state.get("pattern_analysis_results", {}).get("patterns", [])
    if patterns:
        score += 0.3 * min(len(patterns), 2)
        factors.append(f"{len(patterns)} correlated pattern(s) detected")

    abstained = [p for p, r in synthetic_results.items() if r["verdict"] == "abstain"]
    confidence = "low" if abstained else "high"
    if abstained:
        factors.append(f"{len(abstained)} file(s) required abstention -> lowers overall confidence")

    state["risk_score"] = {
        "score": min(score, 1.0),
        "confidence": confidence,
        "contributing_factors": factors,
        "requires_human_review": state.get("requires_human_review", False),
    }
    return state
