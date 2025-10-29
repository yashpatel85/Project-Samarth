# Project Samarth: Intelligent Q&A over India's Agricultural Data

**Submission for Build for Bhaarat Fellowship 2026 (Data Science Domain)**

## 🚀 Introduction & Vision

Project Samarth addresses the challenge of accessing and interpreting the vast, valuable datasets published by the Indian Government on portals like `data.gov.in`. These portals contain high-granularity data crucial for policy-making, research, and public understanding, particularly concerning the nation's agricultural economy. However, the data exists in varied formats, is often inconsistent, and lacks unified query interfaces.

The vision of Project Samarth is to bridge this gap by providing an **intelligent, conversational Q&A system**. This system allows users (like policymakers, researchers, or citizens) to ask complex questions in natural language about India's agricultural production and market prices, receiving accurate, data-backed answers derived directly from live government sources, complete with visualizations.

## 🚧 The Challenge

Building this system presented several key challenges:

1.  **Data Discovery & Accessibility:** The `data.gov.in` portal, while comprehensive, suffers from inconsistent metadata, difficult search functionality, and unreliable API endpoints. Many listed `resource_id`s lead to errors ("Meta not found") or empty datasets. Programmatic discovery via API was initially attempted but proved infeasible, requiring a pivot to manual identification of stable resource IDs.
2.  **Data Heterogeneity:** Datasets from different sources (e.g., crop production vs. market prices) use different column names, units, time formats, and granularities, requiring robust cleaning and merging logic *at query time*.
3.  **Live Data Requirement:** The system needed to query *live* data, ruling out static databases and necessitating real-time fetching and processing.
4.  **Complex Queries:** Users need to ask questions involving filtering, aggregation, comparisons, trends, correlations, and rankings across potentially multiple datasets.
5.  **Development Environment:** Significant challenges were encountered with Python dependencies, particularly conflicts between core libraries (`google-api-core`, `protobuf`, `pydantic`) and framework packages (`langchain`), requiring meticulous environment management (ultimately using Conda with specific Python versions and careful package installation).

## 💡 Solution & Architecture: The "Samarth-Agent"

Project Samarth employs an **agentic RAG (Retrieval-Augmented Generation)** architecture, utilizing a Large Language Model (LLM - Google Gemini) as a reasoning engine to orchestrate custom tools.

**Core Components:**

1.  **FastAPI Backend:** Provides an API endpoint (`/chat`) to receive user queries. Manages the agent instance.
2.  **LangChain Agent Executor:** Uses the Gemini LLM (`gemini-pro-latest`) configured with a detailed system prompt. The agent follows a ReAct (Reason + Act) loop.
3.  **Custom Tools:**
    * **`get_data`:** Fetches data directly from specified `data.gov.in` resource IDs using their API, returning a Pandas DataFrame and the dataset title (for citation). This ensures access to live data.
    * **`analyze_data` (Code Interpreter):** Executes LLM-generated Python code (primarily using Pandas, Matplotlib, Seaborn) in a controlled environment. This allows for dynamic, flexible analysis, cleaning, merging, aggregation, and visualization generation *on the fly*, directly addressing the data heterogeneity and complex query challenges. Plots are saved and returned as base64 strings.
4.  **Streamlit Frontend:** A simple, interactive chat interface allowing users to ask questions and view text responses along with generated plots.

**Tech Stack:**

* **Backend:** Python, FastAPI, Uvicorn
* **Frontend:** Streamlit
* **Agent/LLM:** LangChain, Google Gemini API (`langchain-google-genai`)
* **Data Handling:** Pandas, Requests
* **Plotting:** Matplotlib, Seaborn
* **Environment:** Conda (Python 3.11), `python-dotenv`

**Design Rationale:**

* **Agentic Approach:** Chosen for its ability to break down complex questions, interact with tools dynamically, and handle unforeseen data variations.
* **Code Execution Tool:** Essential for performing arbitrary data analysis requested by the user without pre-defined analytical functions. Allows maximum flexibility and leverages the power of Pandas for handling inconsistencies.
* **Live API Calls:** Directly meets the requirement of using live data, ensuring relevance.
* **Separate Frontend/Backend:** Standard practice for web applications, allowing scalability and separation of concerns.

## 📊 Data Sources Used

After extensive testing due to API instability, the prototype primarily uses the following confirmed working `data.gov.in` resources:

1.  **Crop Production:**
    * **Title:** "District-wise, season-wise crop production statistics from 1997"
    * **Resource ID:** `35be999b-0208-4354-b557-f6ca9a5355de`
    * **Provides:** District-level production (Tonnes) and area (Hectares) by crop, year, and season.
2.  **Market Prices:**
    * **Title:** "Current Daily Price of Various Commodities from Various Markets (Mandi)"
    * **Resource ID:** `9ef84268-d588-465a-a308-a864a43d0070`
    * **Provides:** Market-level daily min, max, and modal prices by commodity and variety.

*(Initial exploration included climate datasets (rainfall), but stable, programmatically accessible resources could not be reliably identified during development, demonstrating the real-world challenges highlighted by the project brief).*

## ✨ Key Features

* **Natural Language Querying:** Understands complex questions about agricultural data.
* **Live Data Fetching:** Connects directly to `data.gov.in` APIs.
* **Dynamic Data Analysis:** Generates and executes Python/Pandas code on-the-fly for filtering, aggregation, calculations, and merging.
* **Visualization:** Generates bar charts and line plots using Matplotlib/Seaborn based on user requests.
* **Source Citation:** Automatically includes the title of the source dataset in responses.
* **Handles Data Limitations:** Can recognize and report when specific data requested is not found within the fetched records.
* **Handles Out-of-Scope Questions:** Politely declines queries unrelated to its agricultural data domain.

## ✅ Addressing Evaluation Criteria

* **Problem Solving & Initiative:** Demonstrated by navigating the unreliable `data.gov.in` APIs, pivoting from non-functional resource IDs to stable ones, overcoming significant Python dependency conflicts, and implementing the code execution tool as a flexible solution to data heterogeneity.
* **System Architecture:** Implemented a well-reasoned agentic RAG architecture with custom tools for live data access and dynamic analysis. The separation of frontend, backend, and agent logic promotes modularity. The code execution approach is a key design choice for handling diverse analytical needs.
* **Accuracy & Traceability:** Calculations are performed by executing specific Pandas code, ensuring computational accuracy based on the source data. Source dataset titles are automatically cited.
* **Adherence to Core Values:**
    * *Accuracy:* Prioritized through direct code execution on live data.
    * *Traceability:* Ensured by returning source dataset titles.
    * *Data Security:* API keys are managed securely using `.env` locally and environment variables in deployment (Render), and are not committed to version control (`.gitignore`). The code execution tool runs within the application's environment (for production, this would ideally be further sandboxed, e.g., Docker-within-Docker or a dedicated execution service).

## 🔗 Live Demo

You can interact with the deployed prototype here:

**[https://project-samarth-agent.streamlit.app/]**

*(Note: The backend is hosted on Render's free tier, which may spin down after inactivity, causing the first request to be slow. Google API free tier rate limits (approx. 2 requests/minute) may also be encountered during heavy use.)*

## 🛠️ Setup & Run (Local)

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/yashpatel85/Project-Samarth.git](https://github.com/yashpatel85/Project-Samarth.git)
    cd Project-Samarth
    ```
2.  **Create Conda Environment:** (Requires Anaconda or Miniconda installed)
    ```bash
    conda create -n samarth_env python=3.11 -y
    conda activate samarth_env
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Create `.env` File:**
    * Create a file named `.env` in the project root (`Project-Samarth/`).
    * Add your API keys:
        ```ini
        GOOGLE_API_KEY="YOUR_GOOGLE_AI_STUDIO_KEY"
        DATA_GOV_API_KEY="YOUR_DATA_GOV_IN_KEY"
        ```
5.  **Run Backend Server:**
    * Open a terminal in the project root.
    * Ensure `(samarth_env)` is active.
    * Run: `python backend/run.py`
    * The server will run on `http://127.0.0.1:8000`.
6.  **Run Frontend App:**
    * Open a *second* terminal in the project root.
    * Ensure `(samarth_env)` is active.
    * Run: `streamlit run frontend/app.py`
    * Streamlit will open the app in your browser, likely at `http://localhost:8501`.

## ⚠️ Known Limitations

* **Rate Limits:** The Google Gemini API free tier has strict rate limits (approx. 2 requests per minute). Complex queries requiring multiple LLM calls may hit this limit, causing errors or delays.
* **Data Volume:** Fetching very large datasets (`limit` > 50,000-100,000) might strain memory or exceed timeouts, especially on free deployment tiers.
* **Data Quality/Completeness:** The agent's answers are entirely dependent on the data available via the specific `data.gov.in` resource IDs. Missing or incorrect data in the source will be reflected in the output.
* **Code Execution Security (Prototype Level):** The current implementation executes LLM-generated code within the main backend process. For a production system, this requires significantly more robust sandboxing (e.g., executing code in separate, restricted Docker containers or using specialized secure execution environments).

## 🚀 Future Enhancements

* **Data Caching:** Implement caching for `data.gov.in` API responses to improve speed and reduce load.
* **More Datasets:** Integrate additional relevant datasets (e.g., weather, state-level budgets, fertilizer data) by identifying stable resource IDs.
* **Advanced Analysis:** Enhance the agent's prompt and potentially the code interpreter tool to support more sophisticated statistical analysis or time-series modeling.
* **Robust Sandboxing:** Implement secure sandboxing for the code execution tool.
* **Streaming Responses:** Modify the backend/frontend to stream the agent's thoughts and final answer for better UX on long queries.
* **Error Handling:** Improve handling of API errors (rate limits, timeouts, data errors) with user-friendly messages and potential retries.