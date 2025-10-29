import pandas as pd
import json
import io
import sys
from contextlib import redirect_stdout
import matplotlib.pyplot as plt
import seaborn as sns
import tempfile # For creating temporary files
import base64   # For encoding the image
import os

from .data_fetch import fetch_data_from_resource

def run_python_code(code: str, dataframes: dict[str, pd.DataFrame]) -> str:
    """
    Executes Python code, captures stdout, and saves any generated plot
    to a temporary file, returning the plot as a base64 encoded string.

    Args:
        code (str): The Python code to execute.
        dataframes (dict): DataFrames accessible to the code (e.g., {'df_crop': df}).

    Returns:
        str: Captured stdout text. If a plot is generated and saved via
             plt.savefig(), the output will include a line like:
             "[Plot saved: base64_encoded_image_string]"
             Returns an error message on failure.
    """
    plot_output = None
    stdout_capture = io.StringIO()

    try:
        # Create a temporary file *without* automatically deleting it
        # We'll handle deletion after reading it
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_plot_file:
            temp_plot_filename = temp_plot_file.name

        # Safe environment: Add plotting libraries and the temp filename
        safe_globals = {
            'pd': pd,
            'json': json,
            'plt': plt,
            'sns': sns,
            '__plot_filename__': temp_plot_filename, # Pass filename to the code
            **dataframes
        }

        # Redirect stdout and execute code
        with redirect_stdout(stdout_capture):
            # IMPORTANT: Add plot closing logic to the user's code
            # This ensures plots don't linger in memory
            code_to_execute = code + "\nplt.clf()\nplt.close('all')"
            exec(code_to_execute, safe_globals, {})

        # Check if a plot file was actually created/modified
        # The code MUST call plt.savefig(__plot_filename__)
        if os.path.exists(temp_plot_filename) and os.path.getsize(temp_plot_filename) > 0:
            # Read the saved plot and encode it
            with open(temp_plot_filename, "rb") as f:
                image_bytes = f.read()
                plot_output = base64.b64encode(image_bytes).decode('utf-8')
            print(f"Plot generated and saved to {temp_plot_filename}") # Debug print
        else:
             print("No plot file generated or file is empty.") # Debug print

    except Exception as e:
        # Clean up the temp file if it exists, even on error
        if 'temp_plot_filename' in locals() and os.path.exists(temp_plot_filename):
            os.remove(temp_plot_filename)
        return f"[Error executing code]: {str(e)}"
    finally:
        # Always clean up the plot file if it exists
        if 'temp_plot_filename' in locals() and os.path.exists(temp_plot_filename):
             try:
                 os.remove(temp_plot_filename)
             except OSError:
                 pass # Ignore error if file already removed or inaccessible

    # Combine stdout and plot output
    final_output = stdout_capture.getvalue()
    if plot_output:
        final_output += f"\n[Plot saved: {plot_output}]" # Add encoded string marker

    if not final_output:
        return "[No output was printed. The code ran successfully.]"

    return final_output