import torch
from transformers import AutoModelForMaskedLM, AutoTokenizer
import os
from inference import generate_identifier_candidates, select_best_identifier

class Model:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self, model_path="../model_artifacts/"):
       
        """Loads the model and tokenizer."""
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/graphcodebert-base")
        self.model = AutoModelForMaskedLM.from_pretrained("microsoft/graphcodebert-base").to(self.device)

        # Construct the path to the specific model state dictionary
        model_state_dict_path = os.path.join(model_path, "model_26_2")

        # Check if the file exists before attempting to load it
        if os.path.exists(model_state_dict_path):
            self.model.load_state_dict(torch.load(model_state_dict_path, map_location=self.device))
            self.model.eval()
            print("Model loaded successfully.")
        else:
            print(f"Model state dict not found at {model_state_dict_path}")

    def predict_identifier(self, code_snippet, identifier_location, num_tokens):
        """
        Predicts identifier names using the loaded model.
        """
        if num_tokens == -1:
            # Automatic mode: Select best identifier based on PLL
            best_name = select_best_identifier(code_snippet, self.model, self.tokenizer)
            return [best_name], [1.0] # You might want to return a confidence score or PLL here
        else:
            # Manual mode: Generate candidates with a specific number of tokens
            name, pll = generate_identifier_candidates(code_snippet, num_tokens, self.model, self.tokenizer)
            return [name], [pll]

model_instance = Model()
model_instance.load_model()