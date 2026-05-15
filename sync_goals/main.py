import sys
import os

# Add root to path so we can import modules correctly if run from root
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from sync_goals import auth, api, logic, config

def main():
    if not all([config.DATAVERSE_URL, config.TENANT_ID, config.CLIENT_ID]):
        print("Error: Missing environment variables in .env file.")
        return

    print("--- STARTING GOAL SYNCHRONIZATION ---")
    try:
        token = auth.get_access_token()
        print("Authenticated successfully.")
    except Exception as e:
        print(f"Authentication failed: {e}")
        return

    print(f"\nFetching projects matching filter: {config.PROJECT_FILTER}")
    try:
        projects = api.fetch_projects(token)
        print(f"Found {len(projects)} matching projects.")
    except Exception as e:
        print(f"Error fetching projects: {e}")
        return

    for project in projects:
        logic.sync_project_goals(token, project)

    print("\nModular synchronization complete.")

if __name__ == "__main__":
    main()
