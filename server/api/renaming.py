from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from model import model_instance
import javalang

router = APIRouter(
    prefix = "/rename",
    tags=["renaming"]
)


class RenameRequest(BaseModel):
    code: str
    line: int
    char: int
    num_tokens: int = -1


class RenameResponse(BaseModel):
    suggestions: list[str]
    probabilities: list[float]  




def find_variable_at_position(code, line, char):
    """
    Finds the variable name at the specified (line,char) in the code
    and collects all its occurrences by scanning tokenizer tokens only.
    This avoids the need for valid Java AST parsing.
    """
    try:
        tokens = list(javalang.tokenizer.tokenize(code))
        
        # 1) Find the token at (line, char)
        found_token = None
        for t in tokens:
            if t.position and t.position.line == line:
                start_col = t.position.column
                end_col = start_col + len(t.value) - 1
                if start_col <= char <= end_col:
                    found_token = t
                    break
        
        # 2) Check if we found a token
        if not found_token:
            return None, None, "No token found at that position."
        if not isinstance(found_token, javalang.tokenizer.Identifier):
            return None, None, "Token at position is not an identifier."

        variable_name = found_token.value
        
        # 3) Find all occurrences of that token in the code
        occurrences = []
        for t in tokens:
            if isinstance(t, javalang.tokenizer.Identifier) and t.value == variable_name:
                occurrences.append([t.position.line, t.position.column])

        return variable_name, occurrences, None

    except Exception as e:
        return None, None, f"Error parsing Java code: {e}"

def mask_code(code, occurrences, num_tokens):
    """
    Masks the occurrences of an identifier in the given Java code.
    
    Args:
        code: The Java code as a string.
        occurrences: A list of tuples, each containing the (line, character) position of an occurrence of the identifier.
        num_tokens: The number of tokens to mask.

    Returns:
        The masked code as a string.
    """
    
    lines = code.split('\n')
    for line, char in occurrences:
        line_index = line - 1
        char_index = char - 1
        
        # Ensure the line index is within bounds
        if 0 <= line_index < len(lines):
            line_content = lines[line_index]
            
            # Find the start and end of the identifier
            start = char_index
            while start > 0 and line_content[start - 1].isalnum() or line_content[start - 1] == '_':
                start -= 1
            end = char_index
            while end < len(line_content) and line_content[end].isalnum() or line_content[end] == '_':
                end += 1
            
            # Replace the identifier with [MASK] tokens
            if num_tokens == -1:
                lines[line_index] = line_content[:start] + "[MASK]" + line_content[end:]
            else:
                lines[line_index] = line_content[:start] + " ".join(["[MASK]"] * num_tokens) + line_content[end:]

    masked_code = '\n'.join(lines)
    return masked_code


@router.post("/", response_model=RenameResponse)
async def rename_identifier(request: RenameRequest):
    """
    Renames an identifier in a given Java code snippet.
    """
    try:
        print(request.code)
        print(request.line)
        print(request.char)
        variable_name, occurrences, error_message = find_variable_at_position(request.code, request.line, request.char)

        print(variable_name)
        print(occurrences)

        if error_message:
            raise HTTPException(status_code=400, detail=error_message)

        if not occurrences:
            raise HTTPException(status_code=404, detail=f"Variable '{variable_name}' not found in the code.")

        masked_code = mask_code(request.code, occurrences, request.num_tokens)

        print(masked_code)
        print_str, probabilities = model_instance.predict_identifier(
            masked_code, (request.line, request.char), request.num_tokens
        )

        print(f"Predicted identifier: {print_str}")
        print(f"Probabilities: {probabilities}")
        return RenameResponse(suggestions=[print_str[0]], probabilities=[probabilities[0]])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))