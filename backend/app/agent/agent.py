import os
import json
import pandas as pd
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

from .tools.data_fetch import fetch_data_from_resource
from .tools.code_interpreter import run_python_code

dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in .env file")

CROP_PRODUCTION_ID = "35be999b-0208-4354-b557-f6ca9a5355de"
CROP_PRICE_ID = "9ef84268-d588-465a-a308-a864a43d0070"


SYSTEM_PROMPT = """
You are Samarth-Agent, an expert data analyst. Your mission is to answer complex questions about the Indian agricultural economy.
You must answer by reasoning and using your available tools. You cannot answer from your own knowledge.

**DATA SOURCES:**
You have access to two live datasets, which you can load using the `get_data` tool:
1.  `crop_production`: Contains district-level crop production (volume in tonnes) and area.
    - Key Columns: `state_name`, `district_name`, `crop_year`, `season`, `crop`, `area_`, `production_`
2.  `crop_prices`: Contains daily market-level prices for commodities.
    - Key Columns: `state`, `district`, `market`, `commodity`, `arrival_date`, `min_price`, `max_price`, `modal_price`

**TOOLS:**
You MUST use the following JSON format to call a tool. Do not add any other text outside the JSON block.
{
  "tool_call": {
    "name": "tool_name",
    "args": {
      "arg_name": "value"
    }
  }
}

**Tool 1: get_data**
Loads data from one of the live sources into memory. You must do this before you can analyze.
- `name`: "get_data"
- `args`:
  - `dataset_name` (str): The name of the dataset. Must be one of ["crop_production", "crop_prices"].
  - `limit` (int, optional): Number of records to fetch. Default is 5000. Use a larger limit if you need more data (e.g., for state-wide analysis).
- Returns: A status message (e.g., "Successfully loaded 5000 records into df_crop").

# (Keep DATA SOURCES and Tool 1 description)

**Tool 2: analyze_data**
Runs Python code (using Pandas as `pd`, json, matplotlib.pyplot as `plt`, seaborn as `sns`) to analyze the data you've loaded. Loaded data is available in DataFrames named `df_crop` and `df_price`.
- `name`: "analyze_data"
- `args`:
  - `code` (str): A multi-line string of Python code. MUST use `print()` to output ALL findings and results clearly.
- **Plotting:** If the user asks for a plot or visualization:
    - Generate the plot using `plt` or `sns`.
    - **YOU MUST save the plot by calling `plt.savefig(__plot_filename__)`**. Do not use `plt.show()`.
    - The tool will automatically capture the saved plot.
- Returns: The text output from your `print()` statements. If a plot was saved, the output will also include `[Plot saved: base64_encoded_image_string]`.

**IMPORTANT ANALYSIS GUIDELINES for your Python code:**
1.  **Clean Data First:** (Keep existing cleaning instructions)
    * ...
    * ...
2.  **Perform Calculations:** (Keep existing calculation instructions)
    * ...
    * ...
3.  **Generate Plots (If Requested):**
    * Create clear plots (line plots for trends, bar charts for comparisons).
    * **Always add titles and axis labels (`plt.title()`, `plt.xlabel()`, `plt.ylabel()`)**.
    * Use `plt.xticks(rotation=45)` if x-axis labels overlap.
    * **Crucially, end your plotting code with `plt.savefig(__plot_filename__)`**.
4.  **Output Clearly:** Use `print()` statements... (Keep existing output instructions)

4.  **Synthesize Final Answer:** Once your `analyze_data` tool has returned its output, **STOP calling tools**. Your final response should ONLY contain the natural-language answer summarizing the findings based on the tool output. DO NOT include JSON or code.
        * If all requested data was found, summarize it.
        * **If data for some requested items was missing:** Clearly state which items were missing and why (e.g., "within the fetched records"). Then, present the findings for the data that *was* found.
        * **If a plot was generated:** Mention that the plot is displayed below. If the plot only shows partial data due to missing items, briefly explain this (e.g., "The chart below shows data only for Andhra Pradesh as data for Tamil Nadu was not found."). Ensure your plotting code adjusts titles appropriately if possible."""

class SamarthAgent:

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro-latest", google_api_key=GOOGLE_API_KEY, temperature=0.0)

        self.last_plot_data = None

        # Data storage
        self.df_crop = pd.DataFrame()
        self.df_price = pd.DataFrame()

        # For citations
        self.crop_title = ""
        self.price_title = ""
        self.data_loaded = set()

        self.resource_ids = {
            "crop_production": CROP_PRODUCTION_ID,
            "crop_prices": CROP_PRICE_ID
        }

    
    def _get_data(self, dataset_name: str, limit: int = 5000) -> str:
        """Helper function to call our data_fetch tool."""
        if dataset_name not in self.resource_ids:
            return f"Error: Unknown dataset '{dataset_name}'. Use 'crop_production' or 'crop_prices'."

        resource_id = self.resource_ids[dataset_name]
        df, title = fetch_data_from_resource(resource_id, limit=limit)

        if df.empty:
            return f"Error: Failed to fetch data for '{dataset_name}'."

        if dataset_name == "crop_production":
            self.df_crop = df
            self.crop_title = title
            self.data_loaded.add("crop_production")
            # --- CORRECT LOG MESSAGE FOR CROP ---
            return f"Successfully loaded {len(df)} records into `df_crop` (Source: {title})"
        # --- MISSING ELSE BLOCK ---
        elif dataset_name == "crop_prices": # Using elif for clarity
            self.df_price = df
            self.price_title = title
            self.data_loaded.add("crop_prices")
            # --- CORRECT LOG MESSAGE FOR PRICE ---
            return f"Successfully loaded {len(df)} records into `df_price` (Source: {title})"
        else:
             # Should not happen due to the check at the start, but good practice
             return f"Error: Unhandled dataset name '{dataset_name}' after fetching."
        

    def _analyze_data(self, code: str) -> str:
        """Helper function to call our code_interpreter tool."""
        
        # Check if the code *mentions* a df that isn't loaded (preventive check)
        if "df_crop" in code and self.df_crop.empty:
            return "Error: `df_crop` is referenced in code but not loaded. Call `get_data('crop_production')` first."
        if "df_price" in code and self.df_price.empty:
            return "Error: `df_price` is referenced in code but not loaded. Call `get_data('crop_prices')` first."
            
        # Build the dictionary of *currently loaded* dataframes to pass to the interpreter
        dataframes_to_pass = {}
        if not self.df_crop.empty:
            dataframes_to_pass["df_crop"] = self.df_crop
        if not self.df_price.empty:
            dataframes_to_pass["df_price"] = self.df_price

        # The run_python_code function will handle errors during execution
        return run_python_code(code, dataframes_to_pass)
    
    def _parse_llm_response(self, response) -> (dict | None, str | None):
        """
        Parses the LLM's response robustly to find the FIRST valid tool call
        or assemble the final answer text. Handles complex content structures.

        Returns:
            tuple: (tool_call_dict, None) if a valid tool call is found.
                (None, final_answer_string) if no tool call found and text exists.
                (None, error_string) if parsing fails badly.
        """
        # --- Defensive Checks ---
        if not isinstance(response, AIMessage):
            print(f"Warning: Expected AIMessage, but got {type(response)}")
            return None, f"Agent received an unexpected response type: {type(response)}"
        if not hasattr(response, 'content'):
            print("Warning: AIMessage response object has no 'content' attribute.")
            return None, "Agent received a response with no content."

        content = response.content
        potential_tool_call_json = None
        final_answer_parts = []

        # --- Process Content (String or List) ---
        content_list = [content] if isinstance(content, str) else content

        if isinstance(content_list, list):
            for item in content_list:
                item_text = ""
                if isinstance(item, str):
                    item_text = item.strip()
                elif isinstance(item, dict) and 'text' in item:
                    item_text = item['text'].strip()
                else:
                    # Collect unexpected parts as part of final answer (for debugging)
                    final_answer_parts.append(f"[Unexpected Content Part: {str(item)}]")
                    continue # Skip parsing this part

                # --- Prioritize Finding the FIRST Tool Call ---
                if potential_tool_call_json is None and item_text.startswith("{") and item_text.endswith("}"):
                    try:
                        data = json.loads(item_text)
                        if isinstance(data, dict) and "tool_call" in data:
                            tool_call_content = data["tool_call"]
                            if isinstance(tool_call_content, dict) and "name" in tool_call_content:
                                # Found the first valid tool call, store it and stop looking
                                potential_tool_call_json = tool_call_content
                                print(f"Parser found valid tool call: {potential_tool_call_json.get('name')}")
                                # Don't break yet, collect remaining text for potential final answer if tool call fails upstream
                    except json.JSONDecodeError:
                        # Invalid JSON, treat as text
                        final_answer_parts.append(item_text)
                    except Exception as e:
                        print(f"Error parsing potential JSON tool call item: {e}")
                        final_answer_parts.append(item_text) # Treat as text on error
                else:
                    # Not a potential tool call JSON, add to final answer parts
                    if item_text: # Avoid adding empty strings
                        final_answer_parts.append(item_text)
        else:
            # Content was not a string or list
            print(f"Warning: LLM response content has unexpected type: {type(content)}")
            return None, f"Agent response content had an unexpected format: {str(content)}"


        # --- Return Based on Findings ---
        if potential_tool_call_json:
            # If we found a tool call, return it, ignore any text found after it for now
            return potential_tool_call_json, None
        else:
            # No tool call found, assemble final answer from text parts
            final_answer = "\n".join(final_answer_parts).strip()
            if final_answer:
                print("Parser returning final answer text.")
                return None, final_answer
            else:
                # Handle cases where parsing results in empty text
                print("Warning: LLM response parsed to empty text and no tool call found.")
                return None, "[Agent produced an empty response after parsing.]"
    
    def run(self, query: str, max_turns: int = 5) -> tuple[str, str | None]:
        """
        Runs the main agent reasoning loop.

        Returns:
            tuple: (final_answer_string, base64_plot_data_or_None)
        """
        self.last_plot_data = None # Reset plot data for this run
        message_history = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=query)
        ]

        print(f"--- New Query: {query} ---")

        for i in range(max_turns):
            print(f"\n--- Turn {i+1} ---")
            print(f"Current History (types): {[msg.__class__.__name__ for msg in message_history]}")

            # 1. Call LLM
            try:
                response = self.llm.invoke(message_history)
                # (Keep logging and AIMessage check from previous version)
                raw_content = getattr(response, 'content', '[NO CONTENT ATTRIBUTE]')
                print(f"LLM Raw Response Content: {raw_content}")
                if not isinstance(response, AIMessage):
                    error_msg = f"LLM returned unexpected type: {type(response)}. Content: {raw_content}"
                    print(error_msg)
                    return error_msg, None # Return error and no plot
                message_history.append(response)
            except Exception as llm_err:
                error_msg = f"Error during LLM invocation: {llm_err}"
                print(error_msg)
                return error_msg, None # Return error and no plot

            # 2. Parse response
            tool_call, final_answer = self._parse_llm_response(response)
            print(f"Parsed Tool Call: {tool_call}")
            print(f"Parsed Final Answer: {final_answer}")

            # 3. If it's a final answer, return it WITH any stored plot data
            if final_answer is not None:
                print(f"Agent (Final Answer): {final_answer}")
                # (Keep citation logic)
                citations = []
                # ... (citation appending logic remains the same) ...
                if citations:
                    final_answer += "\n\n**Sources:**\n- " + "\n- ".join(citations)
                # Return final answer AND the stored plot data
                return final_answer, self.last_plot_data

            # 4. If it's a tool call, execute it
            if tool_call is not None:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                print(f"Agent (Executing Tool Call): {tool_name}({tool_args})")

                # --- Inside the 'if tool_call is not None:' block ---
                tool_result = "[TOOL EXECUTION FAILED]" # Default error
                tool_result_str = tool_result # Initialize

                try:
                    # --- Ensure consistent indentation here ---
                    if tool_name == "get_data":
                        # This line MUST be indented relative to the 'if'
                        tool_result = self._get_data(dataset_name=tool_args.get('dataset_name'),
                                                     limit=int(tool_args.get('limit', 5000)))
                        # The result also needs to be converted to string here
                        tool_result_str = str(tool_result)

                    elif tool_name == "analyze_data":
                        # This block MUST be indented relative to the 'elif'
                        tool_result = self._analyze_data(code=tool_args.get('code'))
                        tool_result_str = str(tool_result) # Ensure string initially

                        # --- PLOT HANDLING LOGIC (indented under elif) ---
                        plot_marker = "[Plot saved: "
                        if plot_marker in tool_result_str:
                             start_index = tool_result_str.find(plot_marker)
                             end_index = tool_result_str.find("]", start_index)
                             if end_index != -1:
                                 self.last_plot_data = tool_result_str[start_index + len(plot_marker):end_index]
                                 tool_result_str = tool_result_str[:start_index].strip()
                                 print("Agent extracted plot data from tool result.")
                             else:
                                 print("Warning: Found plot marker but couldn't find end bracket.")
                        # --- END PLOT HANDLING ---

                    else:
                        # This block MUST be indented relative to the 'else'
                        tool_result = f"Error: Unknown tool '{tool_name}'."
                        tool_result_str = tool_result # Re-assign error string

                except Exception as tool_err:
                     # This block MUST be indented relative to the 'except'
                     tool_result_str = f"Error executing tool '{tool_name}': {tool_err}"
                     print(f"!!! Exception during tool execution: {tool_err}") # Add specific log

                # (The rest of the code: print, HumanMessage, append)
                print(f"Tool Result (Text after plot extraction): {tool_result_str[:500]}...")
                result_message = HumanMessage(content=f"[Tool Result: {tool_result_str}]")
                message_history.append(result_message)
                # --- End of 'if tool_call is not None:' block ---

            # (Keep defensive break)
            if final_answer is None and tool_call is None:
                print("Error: Parsing failed to produce tool call or final answer. Stopping.")
                return "Agent parsing failed unexpectedly.", None


        # If max_turns reached
        return f"Agent could not reach a final answer after {max_turns} turns.", self.last_plot_data


# --- Testing Block ---
if __name__ == "__main__":
    agent = SamarthAgent()

    
    query_1 = "What is the total production of 'Rice' in the state 'Andhra Pradesh' for the year 2000? Use the crop_production dataset and fetch 10000 records to be safe."
    answer_1 = agent.run(query_1)
    
    print("\n" + "="*50 + "\n")
    print(f"**Final Answer for Query 1:**\n{answer_1}")
    print("\n" + "="*50 + "\n")

    
    agent_2 = SamarthAgent()
    query_2 = "What are the 3 most common commodities in the 'crop_prices' dataset? Fetch 1000 records."
    answer_2 = agent_2.run(query_2)
    
    print("\n" + "="*50 + "\n")
    print(f"**Final Answer for Query 2:**\n{answer_2}")
    print("\n" + "="*50 + "\n")