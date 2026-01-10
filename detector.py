"""
BiomedCLIP-based skin appearance detector
Model: Microsoft BiomedCLIP (Fine-tuned on 15M+ medical images)
Paper: https://arxiv.org/abs/2303.00915
"""

import logging
from typing import List, Dict, Any

import torch
from PIL import Image

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class CLIPSkinDetector:
    """
    BiomedCLIP-based Top-k skin appearance predictor.

    - Uses GPU with mixed precision if available.
    - Precomputes text embeddings once for all prompts.
    - Returns disease info matching original interface.
    """

    def __init__(self, model_name: str = "hf-hub:microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224"):
        logger.info("Initializing BiomedCLIP detector...")

        try:
            import open_clip
        except ImportError:
            raise ImportError(
                "open_clip_torch is required. Install with: pip install open-clip-torch"
            )

        # Choose device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Running on: {self.device}")

        # Load BiomedCLIP model
        try:
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(model_name)
            self.tokenizer = open_clip.get_tokenizer(model_name)
            logger.info("✓ BiomedCLIP loaded successfully")
        except Exception as e:
            logger.warning(f"BiomedCLIP failed: {e}. Falling back to PubMedCLIP...")
            model_name = "hf-hub:flaviagiammarino/pubmed-clip-vit-base-patch32"
            self.model, _, self.preprocess = open_clip.create_model_and_transforms(model_name)
            self.tokenizer = open_clip.get_tokenizer(model_name)

        self.model.to(self.device)
        self.model.eval()

        # ----------------------
        # DISEASE DEFINITIONS
        # ----------------------
        self.disease_info = self._load_disease_info()

        # Medical prompts for BiomedCLIP (clinical descriptions)
        self.disease_prompts: Dict[str, str] = {
            "psoriasis": "chronic plaque psoriasis with well-demarcated erythematous plaques and silvery scales",
            "eczema": "atopic dermatitis eczema with lichenified pruritic patches and xerosis",
            "melanoma": "cutaneous melanoma with irregular asymmetric borders and color variegation",
            "basal": "basal cell carcinoma with pearly translucent nodule and telangiectasia",
            "actinic": "actinic keratosis showing rough scaly erythematous patch on photodamaged skin",
            "dermatofibroma": "dermatofibroma showing positive dimple sign with hyperpigmented center",
            "benign": "seborrheic keratosis with stuck-on appearance and verrucous surface",
            "melanocytic": "benign melanocytic nevus with uniform pigmentation and symmetric borders",
            "vascular": "benign vascular lesion cherry angioma with bright red papule",
            "acne": "acne vulgaris with comedones papules and pustules",
            "rosacea": "rosacea showing persistent facial erythema and telangiectasia",
            "vitiligo": "Well-defined, depigmented white patches with sharp borders and no surface scaling.",
            "tinea": "tinea corporis ringworm with annular scaling plaque and active peripheral border",
            "urticaria": "acute urticaria showing transient erythematous wheals",
        }

        self.disease_keys: List[str] = list(self.disease_prompts.keys())
        self.disease_texts: List[str] = [
            self.disease_prompts[k] for k in self.disease_keys
        ]

        # Precompute text embeddings
        logger.info("Precomputing text embeddings...")
        self.text_features = self._precompute_text_features()

    # ------------------------------------------------------------
    # DISEASE METADATA
    # ------------------------------------------------------------
    def _load_disease_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Internal metadata used for severity/characteristics.
        """
        return {
            "psoriasis": {
                "name": "Psoriasis-like appearance",
                "severity": "Medium",
                "characteristics": ["Thick plaques", "Silvery scales", "Well-defined borders"],
                "recommendation": "See a dermatologist if patches are spreading, painful, or very itchy."
            },
            "eczema": {
                "name": "Eczema-like appearance",
                "severity": "Low to Medium",
                "characteristics": ["Red patches", "Dry skin", "Itching"],
                "recommendation": "Gentle moisturizer, avoid harsh soaps and known triggers."
            },
            "melanoma": {
                "name": "Irregular dark spot",
                "severity": "High",
                "characteristics": ["Irregular shape", "Multiple colors", "May grow over time"],
                "recommendation": "Seek an in-person dermatology evaluation, especially if changing."
            },
            "basal": {
                "name": "Shiny bump",
                "severity": "Medium to High",
                "characteristics": ["Pearly bump", "May bleed", "Does not heal for weeks"],
                "recommendation": "Consider medical review if spot is persistent or bleeding."
            },
            "actinic": {
                "name": "Rough scaly patch",
                "severity": "Medium",
                "characteristics": ["Scaly patch", "Sun-exposed areas"],
                "recommendation": "Protect from sun and consider in-person evaluation if persistent."
            },
            "dermatofibroma": {
                "name": "Firm brown bump",
                "severity": "Low",
                "characteristics": ["Firm bump", "Brown", "Dimples when pinched"],
                "recommendation": "Often harmless; get checked if changing or symptomatic."
            },
            "benign": {
                "name": "Waxy stuck-on growth",
                "severity": "Low",
                "characteristics": ["Waxy", "Stuck-on look"],
                "recommendation": "Usually harmless; cosmetic removal is optional."
            },
            "melanocytic": {
                "name": "Regular mole",
                "severity": "Low",
                "characteristics": ["Symmetric", "Uniform color"],
                "recommendation": "Monitor for changes in size, color, or shape."
            },
            "vascular": {
                "name": "Small red vascular spot",
                "severity": "Low",
                "characteristics": ["Red spot", "Blanches on pressure"],
                "recommendation": "Often benign; seek review if rapidly changing or symptomatic."
            },
            "acne": {
                "name": "Acne-like bumps",
                "severity": "Low to Medium",
                "characteristics": ["Pimples", "Pustules", "Comedones"],
                "recommendation": "Gentle cleansing, non-comedogenic moisturizer, avoid picking."
            },
            "rosacea": {
                "name": "Redness with small bumps",
                "severity": "Low to Medium",
                "characteristics": ["Redness", "Flushing", "Visible vessels"],
                "recommendation": "Avoid known triggers like heat, spicy foods, and harsh products."
            },
            "vitiligo": {
                "name": "Lighter smooth patches",
                "severity": "Low",
                "characteristics": ["Depigmented patches", "Sharp borders"],
                "recommendation": "Sun protection and in-person guidance if spreading or concerning."
            },
            "tinea": {
                "name": "Ring-like rash",
                "severity": "Low",
                "characteristics": ["Circular", "Itchy", "Raised border"],
                "recommendation": "Keep area dry; over-the-counter antifungal creams are often used."
            },
            "urticaria": {
                "name": "Itchy welts Rash like",
                "severity": "Low to Medium",
                "characteristics": ["Raised welts", "Move around", "Itchy"],
                "recommendation": "Often responds to antihistamines; seek care if severe or persistent."
            },
        }

    # ------------------------------------------------------------
    # PRECOMPUTE TEXT EMBEDDINGS
    # ------------------------------------------------------------
    def _precompute_text_features(self) -> torch.Tensor:
        """
        Precompute normalized text embeddings for all medical prompts.
        """
        text_tokens = self.tokenizer(self.disease_texts).to(self.device)

        with torch.no_grad(), torch.cuda.amp.autocast():
            text_features = self.model.encode_text(text_tokens)
            text_features = text_features / text_features.norm(
                p=2, dim=-1, keepdim=True
            )
        return text_features

    # ------------------------------------------------------------
    # IMAGE FEATURE EXTRACTION
    # ------------------------------------------------------------
    def _extract_image_features(self, image: Image.Image) -> torch.Tensor:
        """
        Extract normalized image features from a PIL image.
        """
        image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad(), torch.cuda.amp.autocast():
            img_features = self.model.encode_image(image_tensor)
            img_features = img_features / img_features.norm(
                p=2, dim=-1, keepdim=True
            )

        return img_features

    # ------------------------------------------------------------
    # TOP-k PREDICTION
    # ------------------------------------------------------------
    def predict(self, image: Image.Image, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Given a PIL image, return top-k appearance predictions.

        Returns a list of dicts:
        [
          {
            "rank": int,
            "confidence": float (0-100),
            "raw_text": str,          # medical description prompt
            "disease": str,           # disease name
            "severity": str,
            "characteristics": list[str],
            "recommendation": str
          },
          ...
        ]
        """
        if top_k <= 0:
            return []

        img_feat = self._extract_image_features(image)

        # Compute similarities (temperature scaling for better calibration)
        temperature = 0.07
        logits = (img_feat @ self.text_features.T) / temperature
        probs = logits.softmax(dim=1)[0]

        # Clamp k to number of classes
        k = min(top_k, len(self.disease_keys))
        top_probs, top_idx = torch.topk(probs, k)

        results: List[Dict[str, Any]] = []
        for rank, (p, idx) in enumerate(zip(top_probs, top_idx), start=1):
            idx = int(idx.item())
            confidence = float(p.item() * 100.0)

            key = self.disease_keys[idx]
            full_text = self.disease_texts[idx]
            info = self.disease_info.get(key, {})

            results.append(
                {
                    "rank": rank,
                    "confidence": confidence,
                    "raw_text": full_text,
                    "disease": info.get("name", key.capitalize()),
                    "severity": info.get("severity", "Unknown"),
                    "characteristics": info.get("characteristics", []),
                    "recommendation": info.get(
                        "recommendation",
                        "Consider gentle skin care and seek in-person advice if concerned.",
                    ),
                }
            )

        return results