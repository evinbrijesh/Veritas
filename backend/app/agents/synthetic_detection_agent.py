"""
Agent 3/9 — Synthetic / AI-generated media detection.
Wraps the two-stage EfficientNet-B4 classifier. Any ABSTAIN verdict
sets requires_human_review=True on the shared state, which the
report-generation agent later respects by NOT auto-finalizing.
"""
from app.agents.state import PipelineState
from app.ml.synthetic_detector import synthetic_detector


def synthetic_detection_agent(state: PipelineState) -> PipelineState:
    results = {}
    needs_review = state.get("requires_human_review", False)

    for path, ingestion_info in state["ingestion_results"].items():
        if ingestion_info["file_type"] not in [".jpg", ".jpeg", ".png"]:
            continue  # video frame extraction would go here in a full build

        detection = synthetic_detector.analyze(path)
        results[path] = {
            "verdict": detection.verdict,
            "confidence": detection.confidence,
            "adversarial_flag": detection.adversarial_flag,
        }
        if detection.verdict == "abstain":
            needs_review = True

    state["synthetic_detection_results"] = results
    state["requires_human_review"] = needs_review
    return state
