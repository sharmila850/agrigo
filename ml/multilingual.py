from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "Varsha00/finetuned-opusmt-en-to-ta"

print("Loading English to Tamil translation model...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

print("Translation model loaded successfully!")


def translate_text(text):
    """
    Translate English text to Tamil.
    """

    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True
    )

    outputs = model.generate(
        **inputs,
        max_length=128
    )

    translated_text = tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    )

    return translated_text


if __name__ == "__main__":

    english_text = "Welcome to AgriConnect"

    tamil_text = translate_text(english_text)

    print("\nEnglish:", english_text)
    print("Tamil:", tamil_text)