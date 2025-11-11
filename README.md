# Notemind

Notemind is an intelligent personal assistant for task and wellness management, designed to work within the MAX messenger. It uses a Large Language Model (LLM) to understand natural language and structure your inputs into a smart schedule.

## Features

*   **Smart Capture (F1):** Input tasks, events, and wellness data through text or voice messages in a single, conversational flow.
*   **AI-Powered Structuring:** Your unstructured text is automatically converted into a structured format (tasks, events, health metrics).
*   **Visual Plan (F3 - In Development):** An interactive calendar to visualize and manage your schedule.
*   **AI Planner (In Development):** Automatic scheduling of new tasks into free slots in your calendar.
*   **Wellness Dashboard (F6 - In Development):** Track your wellness metrics over time with insightful graphs.

## Technology Stack

*   **Backend:** Python, FastAPI
*   **Database:** PostgreSQL with SQLAlchemy
*   **AI/LLM:**
    *   **Language Model:** GigaChat
    *   **Agent Framework:** LangChain, LangGraph
    *   **Speech-to-Text:** SaluteSpeech
*   **Frontend (Mini-app - In Development):** React

## Getting Started

### Prerequisites

*   Python 3.11+
*   PostgreSQL
*   Access to GigaChat and SaluteSpeech APIs

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Notemind
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Set up the database:**
    *   Create a PostgreSQL database (e.g., `notemind`).
    *   Create a `.env` file by copying the `.env.example` and fill in your database credentials and API keys.

4.  **Initialize the database:**
    ```bash
    # TODO: Add a script to run the db initialization
    ```

### Running the Application

```bash
uvicorn main:app --reload
```

The application will be available at `http://localhost:8000`.

You will also need to configure a webhook in your MAX bot settings to point to `http://<your-public-url>/webhook`.
