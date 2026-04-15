from ai_engine import validate_category, validate_description, predict_image_label

# HTML form category → AI label mapping
CATEGORY_MAPPING = {
    "Road Damage": "road",
    "Street Light": "streetlight",
    "Garbage / Sanitation": "garbage",
    "Water Supply": "water_tank",
    "Drainage": "drainage",
    "Other": "other"
}

def check_complaint_with_ai(complaint):
    """
    complaint = {
        category: from HTML form,
        description: user input,
        image_path: full path of uploaded image
    }
    """

    # Normalize category to AI label
    category_label = CATEGORY_MAPPING.get(complaint["category"], "other")

    # 1️⃣ CATEGORY CHECK
    if not validate_category(category_label):
        return False, "Invalid category selected", None, 0

    # 2️⃣ DESCRIPTION CHECK
    if not validate_description(category_label, complaint["description"]):
        return False, "Description does not match category", None, 0

    # 3️⃣ IMAGE CHECK
    predicted_label, confidence = predict_image_label(complaint["image_path"])
    if predicted_label != category_label:
        return False, "Image does not match selected category", predicted_label, confidence

    # ✅ All checks passed
    return True, "AI Verified Successfully", predicted_label, confidence