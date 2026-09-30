from transformers import pipeline


# Load Hugging Face model
classifier = pipeline(
    "image-classification",
    model="Kathir56/plant-disease-tamilnadu"
)

print("Model loaded successfully!")


# Test image
image_path = "test_leaf.jpg"

results = classifier(image_path)


print("\nDisease Prediction:")

for result in results:
    print(
        result["label"],
        "->",
        round(result["score"] * 100, 2),
        "%"
    )