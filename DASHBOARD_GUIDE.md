# BIRD Interactive Dashboard Guide

This guide explains how to open, use, and run actions on the BIRD backend using the interactive single-page application dashboard.

---

## 1. How to Access the Dashboard

1. Make sure your local FastAPI development server is running.
2. Open your web browser and navigate to:
   **`http://localhost:8000/`**
3. Register a new user in the sign-up form and sign in to access the administrator profile.

---

## 2. Sidebar Workspace Selection

- The sidebar displays a **Workspace** selector dropdown.
- Upon first sign-in, the system automatically initializes a default workspace called **"Corporate Intelligence"**.
- To create a new isolated sandbox, click **"+ New Workspace"** and type a name/description. Different workspaces maintain completely separate agent reasoning traces, vault facts, and campaigns.

---

## 3. The 3 Dashboard Categories (How to Use & View Outputs)

### Category A: Control Room (Orchestrator Console)
* **Purpose**: Coordinates multi-agent workflows to analyze business intelligence and run reasoning queries.
* **Actions**:
  1. Input a query in the prompt box (e.g., *"Analyze competitive pricing roadmaps and compile a summary"*).
  2. Select an execution mode:
     - **Adaptive Reasoning (RAR)**: Queries ChromaDB vault memory first, updates retrieval contexts, and reasons through Qwen/Ollama client frameworks.
     - **Sequential**: Runs reasoning stages sequentially.
     - **Parallel**: Ingests competing claims simultaneously.
  3. Click **Execute Agents**.
* **Outputs**:
  - **Execution Monitor Panel**: Displays step-by-step logs in real-time. It traces exactly which agent executed (e.g. `VaultAgent`, `ReasoningAgent`, `DebateAgent`), their reasoning chains, evidence extracted, and individual step confidences.
  - **Final System Output**: Shows the consolidated conclusion, execution runtime in milliseconds, and the average system confidence score.
  - **Reasoning History**: Lists persistent queries in a database log table at the bottom.

---

### Category B: Smart Vault (Agentic RAG Long-Term Memory)
* **Purpose**: Manages long-term semantic memory facts (saved in vector storage) so agents can retrieve them as context.
* **Actions**:
  1. **Ingest Facts**: Type a business claim (e.g., *"Acme Corp pricing starts at $49/month with a 10% discount on yearly subscriptions"*), choose a category, input a source description, and click **Save to Vault**.
  2. **Search Memory**: Enter search terms in the semantic search query box to search vector memory facts.
  3. **Delete Facts**: Click the delete icon (trash can) on any vault fact row to purge it from memory.
* **Outputs**:
  - The **Vault Facts** table displays all active facts stored in the workspace with category tags, source metrics, and indexing confidence rates.

---

### Category C: Campaign Center (Asset Generation & Simulator)
* **Purpose**: Drafts marketing copy (using `ForgeAgent` LLM assets) and simulates channel deployments (using `AttackAgent` analytics engine).
* **Actions**:
  1. Input a campaign name, select a target channel (e.g., *Email Marketing*, *Social Media Ads*, *Web Search*), add a campaign brief, and click **Save Draft Campaign**.
  2. Click **Deploy** on the newly created campaign card to simulate multi-channel asset compilation.
  3. Click **View Analytics** to pull live performance metrics.
* **Outputs**:
  - **Performance Analytics Dashboard**: Shows simulated counters for **Impressions**, **Clicks**, **Conversions**, and **Simulated ROI**.
  - **Conversion Funnel Graph**: Displays a visual progress bar chart representing customer conversion rates through each marketing stage (Impressions -> Clicks -> Conversions).
