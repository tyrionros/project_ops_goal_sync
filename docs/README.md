# Project Goals Sync Tool Documentation

Welcome to the documentation for the Dynamics 365 Project Operations Goals Synchronization Tool. This tool is designed to manage "Generic Goals" within Premium Planners (Project for the Web) efficiently and safely.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Operation Sets (Crucial Concepts)](#operation-sets-crucial-concepts)
3. [The Synchronization Logic](#the-synchronization-logic)
4. [File Descriptions](#file-descriptions)
5. [Getting Started](#getting-started)

---

## Architecture Overview

This project follows a **modular architecture** to separate concerns and ensure maintainability:
- **Root**: Contains the user entry point (`run_me.py`) and configuration files.
- **`sync_goals/` Package**: The core engine of the tool, containing authentication, API interaction, and business logic.
- **`docs/`**: Thorough documentation for end-users and developers.
- **`archived/`**: Legacy versions of the script for historical reference.

---

## Operation Sets (Crucial Concepts)

When working with **Premium Planners** in Dynamics 365, standard Dataverse "Create", "Update", or "Delete" operations are blocked for scheduling entities like Project Goals. Instead, you must use the **Project Schedule API**.

### What is an Operation Set?
An Operation Set is a **transactional container** used by the Project Scheduling Service (PSS). Because the scheduling engine runs independently of the main Dataverse database, changes must be batched and "submitted" to the engine to ensure consistency.

### The Flow of an Operation Set:
1.  **Open**: Call `msdyn_CreateOperationSetV1` to get a unique `OperationSetId`.
2.  **Queue**: Add operations (Create, Update, Delete) to this set using actions like `msdyn_PssCreateV1`. These are **not** committed yet.
3.  **Execute**: Call `msdyn_ExecuteOperationSetV1`. This triggers the background scheduling engine to process the entire batch.
4.  **Abandon (Safety)**: If any operation fails during the queuing phase, we call `msdyn_AbandonOperationSetV1` to clear the set and avoid hitting the "10 open sets per user" limit.

---

## The Synchronization Logic

The tool uses an **Intelligent Sync** approach to stay within the **10-goal limit** per project:

1.  **Mapping**: It first checks for explicit "Old Name -> New Name" mappings.
2.  **Fuzzy Matching**: Any existing goals not in the mapping are compared against the desired 10 goals using a string similarity algorithm (Fuzzy Matching). The closest match is renamed.
3.  **Creation**: If a target goal is still missing after matching, it is created.
4.  **Deletion**: If there are more than 10 goals, the extras are removed.

---

## File Descriptions

### Root Directory
- **`run_me.py`**: The "Smart Runner". It checks if your Python environment has the required libraries and installs them if missing before launching the sync tool.
- **`.env`**: Stores your Environment URL and Azure AD Application details.
- **`requirements.txt`**: Lists the necessary Python packages (`msal`, `requests`, `python-dotenv`).

### `sync_goals/` Folder (The Package)
- **`main.py`**: The orchestrator. Coordinates between auth, API, and logic modules.
- **`config.py`**: The single source of truth for your goal list, OData filters, and mappings.
- **`auth.py`**: Handles **Interactive OAuth2 Authentication**. Opens a browser for you to log in with your Dynamics 365 account.
- **`api.py`**: The communication layer. Handles all HTTP requests to the Dataverse and Schedule APIs.
- **`logic.py`**: The "Brain". Implements the mapping and fuzzy matching logic to decide which API calls to make.

---

## Getting Started

1.  Follow the [App Registration Guide](../APP_REGISTRATION_GUIDE.md) to set up your Azure AD credentials.
2.  Update your `.env` file with your URL and IDs.
3.  Run the tool:
    ```bash
    python run_me.py
    ```
