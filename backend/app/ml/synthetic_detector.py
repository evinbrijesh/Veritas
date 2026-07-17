"""
Two-stage synthetic/AI-generated image detector.

Stage 1: EfficientNet-B4 binary classifier (real vs. synthetic),
         fine-tuned on a real/GAN/diffusion-generated dataset.
Stage 2: Adversarial-perturbation check — flags images that look
         suspiciously "adversarially smoothed" (an attempt to fool
         stage 1), so the case gets an ABSTAIN verdict + human review
         flag instead of a false "real" classification.

This is a key differentiator vs. tools like Cellebrite/Magnet AXIOM,
which mostly rely on hash-matching against known CSAM databases and
don't catch novel AI-generated material.
"""
import torch
import torch.nn as nn
import timm
from PIL import Image
from torchvision import transforms
from dataclasses import dataclass
from app.config import settings


@dataclass
class DetectionResult:
    is_synthetic: bool
    confidence: float          # 0.0 - 1.0
    adversarial_flag: bool     # True if perturbation detected -> needs human review
    verdict: str               # "real" | "synthetic" | "abstain"


class SyntheticImageDetector:
    def __init__(self, model_path: str = None, device: str = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self._build_model()
        self._load_weights(model_path or settings.SYNTHETIC_DETECTOR_MODEL_PATH)
        self.model.to(self.device).eval()

        self.transform = transforms.Compose([
            transforms.Resize((380, 380)),  # EfficientNet-B4 native input size
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        # Calibrated abstention thresholds — don't force a verdict when
        # the model isn't confident. This is deliberate: a wrong "real"
        # verdict on synthetic CSAM is a much worse failure mode than
        # flagging for human review.
        self.CONFIDENCE_THRESHOLD = 0.85
        self.ADVERSARIAL_THRESHOLD = 0.6

    def _build_model(self) -> nn.Module:
        model = timm.create_model("efficientnet_b4", pretrained=False, num_classes=2)
        return model

    def _load_weights(self, model_path: str):
        try:
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
        except FileNotFoundError:
            # Fine-tuned weights aren't included in this scaffold — this is
            # where you'd drop your trained checkpoint before deployment.
            print(f"[WARN] No weights found at {model_path}. "
                  f"Model is running with random init — for scaffolding only.")

    @torch.no_grad()
    def _stage1_classify(self, image: Image.Image) -> tuple[float, float]:
        """Returns (p_real, p_synthetic)"""
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1).squeeze(0)
        return probs[0].item(), probs[1].item()

    def _stage2_adversarial_check(self, image: Image.Image) -> float:
        """
        Placeholder for adversarial-perturbation detection — e.g. comparing
        model confidence under small input transformations (JPEG recompress,
        slight blur, noise injection). Large confidence swings under benign
        transforms suggest adversarial manipulation designed to fool stage 1.
        Returns a suspicion score 0.0 - 1.0.
        """
        # TODO: implement transform-consistency check
        return 0.0

    def analyze(self, image_path: str) -> DetectionResult:
        image = Image.open(image_path).convert("RGB")
        p_real, p_synthetic = self._stage1_classify(image)
        adversarial_score = self._stage2_adversarial_check(image)

        adversarial_flag = adversarial_score >= self.ADVERSARIAL_THRESHOLD
        confidence = max(p_real, p_synthetic)

        if adversarial_flag or confidence < self.CONFIDENCE_THRESHOLD:
            verdict = "abstain"
        else:
            verdict = "synthetic" if p_synthetic > p_real else "real"

        return DetectionResult(
            is_synthetic=(verdict == "synthetic"),
            confidence=confidence,
            adversarial_flag=adversarial_flag,
            verdict=verdict,
        )


synthetic_detector = SyntheticImageDetector()
