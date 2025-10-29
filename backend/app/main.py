from fastapi import FastAPI
from pydantic import BaseModel
import sys
import os
import re 

current_dir = os.path.dirname(os.path.abspath(__file__))

backend_dir = os.path.dirname(current_dir)

project_root = os.path.dirname(backend_dir)

sys.path.append(project_root)

from backend.app.agent.agent import SamarthAgent

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str

class QueryResponse(BaseModel):
    answer: str
    image_base64: str | None = None

app = FastAPI(title="Project Samarth Agent API")

agent = SamarthAgent()
print("SamarthAgent initialiazed.")



import re # Keep this import

def clean_final_answer(text: str) -> str:
    """
    Extracts the LAST block of natural language text after any potential
    JSON tool calls or code snippets.
    """
    # 1. Remove potential plot markers first
    plot_marker = "[Plot saved: "
    if plot_marker in text:
         start_index = text.find(plot_marker)
         text = text[:start_index].strip() # Keep only text before plot marker

    # 2. Find the index of the LAST closing curly brace '}'
    # This usually marks the end of the last tool call JSON
    last_brace_index = text.rfind('}')

    # 3. If a brace is found, take the text *after* it
    if last_brace_index != -1:
        # Find the start of the next meaningful text block
        # Look for the first newline character after the brace
        next_newline = text.find('\n', last_brace_index)
        if next_newline != -1:
             # Take everything after the newline
             cleaned_text = text[next_newline:].strip()
             # If the result is just whitespace or empty, fallback needed
             if cleaned_text:
                  return cleaned_text
        # Fallback: If no newline or only whitespace after brace,
        # or if no brace was found initially, try removing common prefixes
        # This is less reliable but a decent fallback.
        prefixes_to_remove = [
            '{\n  "tool_call": {', # Common start patterns
            'Based on the analysis',
            'Here is the breakdown'
        ]
        original_text = text # Keep original for final fallback
        for prefix in prefixes_to_remove:
             if text.startswith(prefix):
                 text = text[len(prefix):].strip()
                 break # Stop after removing the first matching prefix
        # Final fallback: If cleaning resulted in empty string, return original (minus plot)
        return text if text else original_text


    # 4. If no closing brace was found, assume the text is already clean (or needs fallback)
    else:
         # Apply the same fallback prefix removal as above
        prefixes_to_remove = [
             '{\n  "tool_call": {',
             'Based on the analysis',
             'Here is the breakdown'
        ]
        original_text = text
        for prefix in prefixes_to_remove:
             if text.startswith(prefix):
                 text = text[len(prefix):].strip()
                 break
        return text if text else original_text

@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    print(f"Received query: {request.query}")
    answer = "[Agent processing failed before completion]"
    image_data = None

    try:
        raw_answer, image_data = agent.run(query=request.query) # Returns tuple
        raw_answer_str = str(raw_answer) if raw_answer is not None else "[Agent returned None]"

        # --- Clean the final answer text ---
        answer = clean_final_answer(raw_answer_str) # Apply the cleanup
        # --- End cleaning ---

        print(f"Agent raw answer: {raw_answer_str[:500]}...") # Log raw before cleaning
        print(f"Agent cleaned answer (text): {answer[:500]}...") # Log cleaned
        if image_data:
            print("Agent answer includes a plot.")

    except Exception as e:
        # (Keep existing error handling)
        print(f"Error during agent execution: {e}")
        answer = f"An error occurred: {e}"
        image_data = None

    finally:
        # (Keep existing finally block for debug prints and return)
        print(f"--- Backend Sending ---")
        answer_str = str(answer) # Use the cleaned answer
        print(f"Answer Text (first 100 chars): {answer_str[:100]}...")
        # ... (rest of finally block remains the same) ...
        return QueryResponse(answer=answer_str, image_base64=image_data)


@app.get("/")
def read_root():
    return {"message": "Samarth Agent API is running."}