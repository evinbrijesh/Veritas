"""
Wrapper around the local Ollama runtime (Qwen2.5 7B). Used by the
report-generation and retrieval agents for reasoning over evidence
that's already been structured by the earlier pipeline stages.

Everything here is offline — no calls leave the department's network.
"""
import ollama
from app.config import settings


class LocalLLMClient:
    def __init__(self, host: str = None, model: str = None):
        self.client = ollama.Client(host=host or settings.OLLAMA_HOST)
        self.model = model or settings.LLM_MODEL_NAME

    def generate(self, prompt: str, system: str | None = None, temperature: float = 0.2) -> str:
        response = self.client.generate(
            model=self.model,
            prompt=prompt,
            system=system,
            options={"temperature": temperature},
        )
        return response["response"]

    def generate_with_reasoning_trace(self, prompt: str, system: str | None = None) -> dict:
        """
        Used for the 'reasoning replay' explainability feature — asks the
        model to separate its reasoning steps from its final conclusion,
        so an investigator can audit *why* the system flagged something.
        """
        structured_system = (system or "") + (
            "\n\nRespond in two clearly labeled sections:\n"
            "REASONING: step-by-step reasoning\n"
            "CONCLUSION: final answer only"
        )
        raw = self.generate(prompt, system=structured_system)

        reasoning, conclusion = raw, raw
        if "CONCLUSION:" in raw:
            parts = raw.split("CONCLUSION:")
            reasoning = parts[0].replace("REASONING:", "").strip()
            conclusion = parts[1].strip()

        return {"reasoning": reasoning, "conclusion": conclusion, "raw": raw}


llm_client = LocalLLMClient()
