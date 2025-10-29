import uvicorn
import os
import sys 


if __name__ == "__main__":
    # Get the directory of the run.py script
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the parent directory (project root)
    project_root = os.path.dirname(backend_dir)

    # --- Explicitly add project root to sys.path --- # <-- Added block
    if project_root not in sys.path:                     # <-- Added block
        sys.path.insert(0, project_root)                 # <-- Added block
    # --- End path modification ---                      # <-- Added block

    

    
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)