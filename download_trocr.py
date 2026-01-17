from transformers import TrOCRProcessor, VisionEncoderDecoderModel

# Where to store the downloaded model locally
CACHE_DIR = "/home/USER/genealogy/cache/models"

# Download processor (tokenizer + preprocessor)
trocr_processor = TrOCRProcessor.from_pretrained(
    "microsoft/trocr-base-handwritten",
    cache_dir=CACHE_DIR
)

# Download the model weights
trocr_model = VisionEncoderDecoderModel.from_pretrained(
    "microsoft/trocr-base-handwritten",
    cache_dir=CACHE_DIR
)

print("TrOCR model and processor downloaded successfully!")

