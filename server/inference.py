import numpy as np
import torch
import torch.nn.functional as F
import random
from transformers import AutoModelForMaskedLM, AutoTokenizer

def generate_identifier_candidates(code_snippet, num_mask_tokens, model, tokenizer):
    """
    Generates identifier name candidates for a masked code snippet using a language model.

    Args:
        code_snippet (str): The Java code snippet with the identifier replaced by [MASK] tokens.
        num_mask_tokens (int): The number of [MASK] tokens to use (representing the desired number of subtokens).
        model (AutoModelForMaskedLM): The pre-trained language model.
        tokenizer (AutoTokenizer): The tokenizer corresponding to the model.

    Returns:
        tuple: A tuple containing:
            - str: The highest-scoring candidate identifier name.
            - float: The rounded average negative log-likelihood (PLL) of the prediction.
    """
    
    # Prepare the input by adding spaces around [MASK] tokens
    X_init = code_snippet
    X_init = X_init.replace("[MASK]", " [MASK] ")
    X_init = X_init.replace("[MASK]", " ".join([tokenizer.mask_token] * num_mask_tokens))

    # Tokenize the input
    tokens = tokenizer.encode_plus(X_init, add_special_tokens=False, return_tensors='pt')
    
    # Split the input into chunks to handle sequences longer than the model's maximum length
    input_id_chunks = tokens['input_ids'][0].split(510)
    mask_chunks = tokens['attention_mask'][0].split(510)

    # Add special tokens ([CLS] and [SEP]) and pad the chunks
    input_id_chunks = [torch.cat([torch.full((1,), fill_value=101), chunk, torch.full((1,), fill_value=102)]) for chunk in input_id_chunks]
    mask_chunks = [torch.cat([torch.full((1,), fill_value=1), chunk, torch.full((1,), fill_value=1)]) for chunk in mask_chunks]
    
    # Pad chunks to the maximum length (512)
    padded_input_ids = [torch.cat([chunk, torch.full((512 - chunk.shape[0],), fill_value=0)]) if chunk.shape[0] < 512 else chunk for chunk in input_id_chunks]
    padded_mask_chunks = [torch.cat([chunk, torch.full((512 - chunk.shape[0],), fill_value=0)]) if chunk.shape[0] < 512 else chunk for chunk in mask_chunks]

    # Find the positions of the masked tokens
    mask_positions = []
    for i, chunk in enumerate(padded_input_ids):
        chunk_mask_positions = []
        for j, token_id in enumerate(chunk):
            if token_id == tokenizer.mask_token_id:
                if j != 0 and padded_input_ids[i][j-1] == tokenizer.mask_token_id:
                    continue
                chunk_mask_positions.append(j)
        mask_positions.append(chunk_mask_positions)

    # Convert lists to tensors
    input_ids = torch.stack(padded_input_ids)
    att_mask = torch.stack(padded_mask_chunks)

    # Move tensors to the same device as the model
    input_ids = input_ids.to(model.device)
    att_mask = att_mask.to(model.device)

    # Model inference
    with torch.no_grad():
        outputs = model(input_ids, attention_mask=att_mask)
        last_hidden_state = outputs.last_hidden_state

    # Aggregate hidden states of masked tokens
    aggregated_states = []
    for t in range(num_mask_tokens):
        token_states = []
        for p in range(len(mask_positions)):
            for mask_pos in mask_positions[p]:
                token_states.append(last_hidden_state[p, mask_pos + t])
        aggregated_states.append(torch.stack(token_states).mean(dim=0))

    # Predict subtokens and calculate PLL
    predicted_name = ""
    total_pll = 0.0
    for i, state in enumerate(aggregated_states):
        top_indices = torch.topk(state, k=5, dim=0).indices
        probs = F.softmax(state, dim=0)
        
        for index in top_indices:
            token = tokenizer.decode(index.item()).strip()
            if token.isalpha():
                predicted_name += token
                total_pll -= torch.log(probs[index]).item()
                break

    avg_pll = round(total_pll / num_mask_tokens, 2)

    return predicted_name, avg_pll

def select_best_identifier(code_snippet, model, tokenizer, max_num_tokens=6):
    """
    Selects the best identifier name for a masked code snippet based on PLL scores 
    across a range of possible subtoken numbers.

    Args:
        code_snippet (str): The Java code snippet with the identifier replaced by [MASK] tokens.
        model (AutoModelForMaskedLM): The pre-trained language model.
        tokenizer (AutoTokenizer): The tokenizer corresponding to the model.
        max_num_tokens (int): The maximum number of subtokens to consider.

    Returns:
        str: The best identifier name based on PLL scores.
    """
    
    best_name = ""
    best_pll = float('inf')

    for num_tokens in range(1, max_num_tokens + 1):
        name, pll = generate_identifier_candidates(code_snippet, num_tokens, model, tokenizer)
        print(f"Prediction with {num_tokens} token(s): {name} (PLL: {pll})")
        if pll < best_pll:
            best_pll = pll
            best_name = name

    return f"The best identifier name (based on PLL) is: {best_name}"