
# IRename: Intelligent Code Renaming Assistant

## Overview

**IRename** is a tool designed to assist developers in renaming identifiers within Java code snippets. Leveraging the power of deep learning, specifically a fine-tuned [GraphCodeBERT](https://huggingface.co/microsoft/graphcodebert-base) model, IRename provides intelligent suggestions for identifier names based on the surrounding code context. This project was developed for the SCAM 2024 research project.

## Features

- **Context-Aware Suggestions:**  IRename analyzes the code context to suggest meaningful and relevant identifier names.
- **Multiple Token Handling:** Supports generating names consisting of multiple subtokens (e.g., `newVariableName`).
- **Automatic and Manual Modes:**
    - **Automatic:**  Determines the optimal number of subtokens for the identifier name using a probabilistic approach (lowest Pseudo-Perplexity, PLL).
    - **Manual:** Allows users to specify the desired number of subtokens.
- **REST API:**  Exposes functionality through a RESTful API, making it easy to integrate with other tools or IDEs.
- **FastAPI Backend:** Built with FastAPI for high performance and easy deployment.
- **javalang-based Tokenizer:**  Uses `javalang` for fast and reliable Java code tokenization, even with invalid or incomplete code.

## Architecture

The system comprises the following key components:

1. **Frontend (Not Included):** While not part of this repository, a frontend (e.g., a VS Code extension) can interact with the API to send code snippets and receive renaming suggestions.
2. **FastAPI Backend (`main.py`):**
    -   Provides the REST API endpoints for code renaming requests.
    -   Handles communication with the core model.
3. **Core Model (`model.py`):**
    -   Loads and utilizes the fine-tuned GraphCodeBERT model.
    -   Implements the logic for generating identifier suggestions, including both automatic and manual subtoken count selection.
4. **Inference Logic (`inference.py`):**
    -   Contains the core functions for generating identifier candidates (`generate_identifier_candidates`) and selecting the best candidate based on PLL (`select_best_identifier`).
5. **API Logic (`renaming.py`):**
    -   Defines the API endpoint (`/rename`) and request/response models.
    -   Handles Java code parsing, identifier occurrence finding, code masking, and calling the `model.py` for prediction.

## How it Works

1. **Code Input:** The user provides a Java code snippet, the line and character position of the identifier to rename, and (optionally) the desired number of subtokens.
2. **Identifier Location:** The `find_variable_at_position` function in `renaming.py` uses `javalang`'s tokenizer to efficiently find the identifier at the given position and all its occurrences within the code snippet.
3. **Code Masking:** The `mask_code` function replaces all occurrences of the identifier with `[MASK]` tokens. The number of `[MASK]` tokens can be specified (manual mode) or dynamically adjusted (automatic mode).
4. **Model Inference:**
    -   The masked code is tokenized and chunked into segments suitable for the GraphCodeBERT model.
    -   The model predicts the most likely tokens to fill in the `[MASK]` positions.
    -   In automatic mode, `select_best_identifier` tries different numbers of subtokens and selects the suggestion with the lowest Pseudo-Perplexity (PLL), indicating the highest confidence.
5. **Suggestion Output:** The API returns the predicted identifier name(s) and their associated probabilities (or PLL).

## Installation

1. **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Download Pretrained Model:**

    - Download the fine-tuned model state dictionary (`model_26_2`) from the provided source or use your own fine-tuned model.
    - Place it in the `model_artifacts/` directory.

## Usage

1. **Start the FastAPI server:**

    ```bash
    uvicorn main:app --reload
    ```

2. **Send a request to the API:**

    You can use tools like `curl` or `Postman` to send POST requests to the `/rename` endpoint.

    **Example `curl` request:**

    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{
        "code": "public class MyClass {\n    public int myVar = 10;\n    public void myMethod() {\n        int x = myVar + 5;\n        System.out.println(x);\n    }\n}",
        "line": 3,
        "char": 13,
        "num_tokens": -1
    }' http://localhost:8000/rename
    ```

    **Expected Response:**

    ```json
    {
        "suggestions": ["<suggested_name>"],
        "probabilities": [<probability_or_pll>]
    }
    ```
    -   `code`: The Java code snippet.
    -   `line`: The line number of the identifier (1-based).
    -   `char`: The character position of the identifier on that line (1-based).
    -   `num_tokens`: The desired number of subtokens for the new identifier. Use `-1` for automatic mode.

## Example

**Input Code:**

```java
public class Example {
    public int counter = 0;

    public void increment() {
        counter++;
    }

    public int getCount() {
        return counter;
    }
}


**Request:**

-   `line`: 2
-   `char`: 16
-   `num_tokens`: -1 (automatic mode)

**Masked Code (sent to the model):**

```java
public class Example {
    public int [MASK] = 0;

    public void increment() {
        [MASK]++;
    }

    public int getCount() {
        return [MASK];
    }
}
```

**Possible Output:**

```json
{
    "suggestions": ["value"],
    "probabilities": [4.56]
}
```

## Limitations

-   **Java Only:** Currently supports only Java code.
-   **Context Window:** The model's context window is limited (512 tokens), so very long code snippets might be truncated, potentially affecting the accuracy of suggestions.
-   **Model Accuracy:** The accuracy of suggestions depends on the quality of the training data and the model's ability to generalize to unseen code.
-   **No Type Information:**  The model doesn't utilize explicit type information, which could be used to improve the accuracy of suggestions in some cases.

## Future Work

-   **Support for other languages:** Extend the system to support other programming languages.
-   **Improved Model Training:**  Explore larger and more diverse training datasets, and experiment with different model architectures.
-   **Integration with IDEs:** Develop plugins for popular IDEs to provide seamless integration.
-   **User Feedback:** Implement mechanisms to collect user feedback on the quality of suggestions to further improve the model.
-   **Incorporate Type Information:** Investigate ways to incorporate type information into the model to improve the accuracy of suggestions.

## Contributing

Contributions are welcome! Please feel free to open issues or submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
```