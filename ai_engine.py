import cv2
import numpy as np
import os

# AI categories
LABELS = ["road", "drainage", "water_tank", "garbage", "streetlight"]

# Keywords to match in description
CATEGORY_KEYWORDS = {
    "road": ["road", "pothole", "street", "crack", "damaged"],
    "water_tank": ["water", "tank", "leak", "overflow", "supply"],
    "garbage": ["garbage", "waste", "dump", "trash", "bin"],
    "streetlight": ["streetlight", "lamp", "light", "pole"],
    "drainage": ["drain", "sewage", "overflow", "blocked"]
}

# ---------------- CATEGORY CHECK ---------------- #
def validate_category(category):
    """
    Check if the category exists in AI labels
    """
    return category in LABELS

# ---------------- DESCRIPTION CHECK ---------------- #
def validate_description(category, description):
    """
    Check if description contains any of the category keywords
    """
    keywords = CATEGORY_KEYWORDS.get(category, [])
    description = description.lower()
    return any(k.lower() in description for k in keywords)

# ---------------- IMAGE CHECK ---------------- #
def predict_image_label(image_path):
    """
    Dummy image classifier: map filename to label
    Replace with CNN model later for real prediction
    """
    if not os.path.exists(image_path):
        return None, 0.0

    fname = os.path.basename(image_path).lower()
    for label in LABELS:
        if label in fname:
            return label, 0.95

    # fallback
    return "other", 0.5