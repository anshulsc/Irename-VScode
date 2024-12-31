import numpy as np
import torch
import torch.nn.functional as F
import random
from transformers import AutoModelForMaskedLM, AutoTokenizer

def generate_identifier_candidates(code_snippet, num_mask_tokens, model, tokenizer):
    """
    Generates an identifier prediction for `code_snippet` (which contains "[MASK]"),
    replacing "[MASK]" with `num_mask_tokens` mask tokens, then performing
    a forward pass and picking the best alphabetical token(s).

    Returns:
        (predicted_identifier, avg_pll)
            predicted_identifier: str
            avg_pll: float
    """

    # 1) Replace the single [MASK] placeholder with `num_mask_tokens` sub-tokens
    X_init = code_snippet.replace("[MASK]", " [MASK] ")
    X_init = X_init.replace("[MASK]", " ".join([tokenizer.mask_token] * num_mask_tokens))

    print(X_init)

    # 2) Tokenize without adding special tokens (we'll add them manually)
    encoding = tokenizer.encode_plus(
        X_init,
        add_special_tokens=False,  # We'll do [CLS]/[SEP] manually
        return_tensors='pt'
    )
    
    input_ids_full = encoding['input_ids'][0]          # shape: [seq_len]

    attention_mask_full = encoding['attention_mask'][0]


    # 3) Split into 510-token chunks (so we can add [CLS]/[SEP])
    # Convert the tuple to a list

    input_id_chunks = list(input_ids_full.split(510))
    mask_chunks     = list(attention_mask_full.split(510))



    # 4) Prepend [CLS] (ID=101) and append [SEP] (ID=102) to each chunk;
    #    also do the same for the attention mask.
    CLS_ID = torch.full((1,), 101, dtype=torch.long)
    SEP_ID = torch.full((1,), 102, dtype=torch.long)
    ATT_1  = torch.full((1,), 1,   dtype=torch.long)
    PAD_0  = torch.full((1,), 0,   dtype=torch.long)


    for i in range(len(input_id_chunks)):
        input_id_chunks[i] = torch.cat([CLS_ID, input_id_chunks[i], SEP_ID], dim=-1)

        mask_chunks[i]     = torch.cat([ATT_1,  mask_chunks[i],     ATT_1 ], dim=-1)

    # 5) Pad each chunk to length 512
    for i in range(len(input_id_chunks)):
        length = input_id_chunks[i].size(0)
        if length < 512:
            pad_len = 512 - length
            input_id_chunks[i] = torch.cat([input_id_chunks[i], PAD_0.repeat(pad_len)], dim=-1)
            mask_chunks[i]     = torch.cat([mask_chunks[i],     PAD_0.repeat(pad_len)], dim=-1)

    # 6) Identify the positions of the first token in each [MASK] block
    mask_positions = []
    for chunk_tensor in input_id_chunks:
        positions = []
        j = 0
        while j < chunk_tensor.size(0):
            if chunk_tensor[j].item() == tokenizer.mask_token_id:
                # If consecutive masks, skip until we find the next block
                positions.append(j)
                while j < chunk_tensor.size(0) and chunk_tensor[j].item() == tokenizer.mask_token_id:
                    j += 1
            else:
                j += 1
        mask_positions.append(positions)


    # 7) Stack for model input
    batch_input_ids = torch.stack(input_id_chunks)   # shape: [n_chunks, 512]
    batch_att_mask  = torch.stack(mask_chunks)       # same shape

    batch_input_ids = batch_input_ids.to(model.device)
    batch_att_mask  = batch_att_mask.to(model.device)

    # 8) Forward pass -> get logits of shape [batch_size, seq_len, vocab_size]
    with torch.no_grad():
        outputs = model(batch_input_ids, attention_mask=batch_att_mask)
        logits = outputs.logits  # or outputs[0]

    # 9) For each subtoken index, gather & average the logits from all chunk positions
    #    If `num_mask_tokens` = 3, we look at positions [mask_pos, mask_pos+1, mask_pos+2].
    subtoken_averages = []
    for t in range(num_mask_tokens):
        # We'll gather the t-th subtoken's logits
        subtoken_logits = []
        for chunk_idx, positions in enumerate(mask_positions):
            for start_pos in positions:
                pos = start_pos + t
                if pos < 512:
                    subtoken_logits.append(logits[chunk_idx, pos])  # shape: [vocab_size]
        if len(subtoken_logits) > 0:
            # Average across all occurrences
            subtoken_averages.append(torch.stack(subtoken_logits).mean(dim=0))
        else:
            # If no positions found, skip (rare edge case)
            pass

    # 10) Decode predicted tokens + accumulate negative log-prob (PLL)
    predicted_identifier = ""
    total_pll = 0.0

    for avg_logit in subtoken_averages:
        prob_vector = F.softmax(avg_logit, dim=-1)
        topk_ids    = torch.topk(avg_logit, k=5).indices

        chosen_str = None
        chosen_id  = None
        for candidate_id in topk_ids:
            tok_str = tokenizer.decode(candidate_id.item()).strip()
            if tok_str.isalpha():  # pick the first alphabetical token
                chosen_str = tok_str
                chosen_id  = candidate_id
                break

        if chosen_str is None:
            # fallback: pick the top token even if not purely alphabetical
            chosen_id  = topk_ids[0]
            chosen_str = tokenizer.decode(chosen_id.item()).strip()

        predicted_identifier += chosen_str
        # Negative log prob = -log(prob of chosen token)
        total_pll -= torch.log(prob_vector[chosen_id]).item()

    # 11) Average PLL over the number of sub-tokens
    avg_pll = 0.0
    if num_mask_tokens > 0:
        avg_pll = round(total_pll / num_mask_tokens, 2)



    return predicted_identifier, avg_pll


def select_best_identifier(code_snippet, model, tokenizer, max_num_tokens=6):
    """
    Equivalent to the 'meet(...)' function style:
    Tries multiple sub-token counts from 1..max_num_tokens,
    picks the best (lowest PLL).
    """

    best_identifier = ""
    best_pll = float('inf')
    logs = []

    # Try subtoken counts 1..max_num_tokens
    for n_sub in range(1, max_num_tokens + 1):
        name, pll = generate_identifier_candidates(code_snippet, n_sub, model, tokenizer)
        logs.append(f"Prediction with {n_sub} token(s): {name} (PLL: {pll})")
        print(logs[-1])

        if pll < best_pll:
            best_pll = pll
            best_identifier = name

    # Optional: print or return the logs
    # for line in logs:
    #     print(line)

    print(f"The best identifier name (based on PLL) is: {best_identifier}")

    return best_identifier