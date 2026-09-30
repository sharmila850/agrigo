def calculate_match(farmer_crop, buyer_requirement):

    score = 0

    # 1. Crop match
    if farmer_crop["crop_name"].lower() == buyer_requirement["crop_name"].lower():
        score += 40

    # 2. Quantity match
    if farmer_crop["quantity"] >= buyer_requirement["quantity"]:
        score += 25

    # 3. Location match
    if farmer_crop["location"].lower() == buyer_requirement["location"].lower():
        score += 15

    # 4. Price match
    if farmer_crop["expected_price"] <= buyer_requirement["max_price"]:
        score += 15

    # 5. Quality match
    if farmer_crop["quality"] == buyer_requirement["quality"]:
        score += 5

    return score