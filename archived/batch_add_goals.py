import os
import requests
import uuid
import json
import sys
from msal import PublicClientApplication
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATAVERSE_URL = os.getenv("DATAVERSE_URL")
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")
# CLIENT_SECRET is not used for PublicClientApplication (Interactive)

# Configuration
API_VERSION = "v9.1"
GOALS_TO_ADD = [
    "P53 Customer Requirements",
    "P53 Technical Requirements",
    "P53 Development & Technical Documentation in Dev environment",
    "P53 Set up IAM in Dev environment",
    "P53 Technical QA Testing in UAT environment",
    "P53 Functional QA Testing in UAT environment",
    "P53 Deployment from Dev to Prod environment",
    "P53 Set up IAM in Prod environment",
    "P53 Technical QA Testing in Prod environment",
    "P53 Functional QA Testing in Prod Environment"
]
PROJECT_FILTER = "contains(msdyn_subject, 'IAM Security')"

def get_access_token():
    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    # Use PublicClientApplication for interactive login
    app = PublicClientApplication(
        CLIENT_ID,
        authority=authority
    )
    
    # Try to get token from cache first
    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(scopes=[f"{DATAVERSE_URL}/.default"], account=accounts[0])
    
    if not result:
        print("No cached token found. Opening browser for interactive login...")
        result = app.acquire_token_interactive(scopes=[f"{DATAVERSE_URL}/.default"])
    
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Could not acquire token: {result.get('error_description')}")

def fetch_projects(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8"
    }
    url = f"{DATAVERSE_URL}/api/data/{API_VERSION}/msdyn_projects?$filter={PROJECT_FILTER}&$select=msdyn_projectid,msdyn_subject"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["value"]

def create_operation_set(token, project_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8"
    }
    url = f"{DATAVERSE_URL}/api/data/{API_VERSION}/msdyn_CreateOperationSetV1"
    
    # Standard parameter for CreateOperationSetV1
    payload = {
        "msdyn_projectid": project_id,
        "msdyn_description": "Batch Goal Creation via Script"
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        # Some environments expect 'ProjectId' instead of 'msdyn_projectid'
        payload = {
            "ProjectId": project_id,
            "Description": "Batch Goal Creation via Script"
        }
        response = requests.post(url, headers=headers, json=payload)
        
    response.raise_for_status()
    return response.json()["OperationSetId"]

def abandon_operation_set(token, operation_set_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8"
    }
    url = f"{DATAVERSE_URL}/api/data/{API_VERSION}/msdyn_AbandonOperationSetV1"
    payload = {"OperationSetId": operation_set_id}
    requests.post(url, headers=headers, json=payload)

def add_goal_to_operation_set(token, operation_set_id, project_id, goal_name):
    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8"
    }
    url = f"{DATAVERSE_URL}/api/data/{API_VERSION}/msdyn_PssCreateV1"
    
    goal_id = str(uuid.uuid4())
    # Note: Passing as an object, not a stringified JSON, to see if it fixes the parsing error
    entity_data = {
        "@odata.type": "Microsoft.Dynamics.CRM.msdyn_projectgoal",
        "msdyn_projectgoalid": goal_id,
        "msdyn_name": goal_name,
        "msdyn_projectid@odata.bind": f"/msdyn_projects({project_id})"
    }
    
    payload = {
        "Entity": entity_data,
        "OperationSetId": operation_set_id
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code not in [200, 204]:
        # Fallback: Try stringified if object fails (some versions vary)
        payload["Entity"] = json.dumps(entity_data)
        response = requests.post(url, headers=headers, json=payload)
        
    if response.status_code not in [200, 204]:
        print(f"  [ERROR] Failed to add goal operation '{goal_name}': {response.text}")
        return False
    else:
        print(f"  [QUEUED] Goal creation operation queued: {goal_name}")
        return True

def execute_operation_set(token, operation_set_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8"
    }
    url = f"{DATAVERSE_URL}/api/data/{API_VERSION}/msdyn_ExecuteOperationSetV1"
    payload = {
        "OperationSetId": operation_set_id
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    print(f"  [SUCCESS] Operation set executed.")

def fetch_existing_goals_count(token, project_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
    }
    url = f"{DATAVERSE_URL}/api/data/{API_VERSION}/msdyn_projectgoals?$filter=_msdyn_projectid_value eq {project_id}&$count=true&$select=msdyn_projectgoalid"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json().get("@odata.count", 0)

def main():
    if not all([DATAVERSE_URL, TENANT_ID, CLIENT_ID]):
        print("Error: Missing environment variables. Please check your .env file.")
        return

    print("--- STARTING BATCH GOAL CREATION (INTERACTIVE MODE) ---")
    try:
        token = get_access_token()
        print("Authenticated successfully.")
    except Exception as e:
        print(f"Authentication failed: {e}")
        return

    print(f"\nFetching projects matching filter: {PROJECT_FILTER}")
    try:
        projects = fetch_projects(token)
        print(f"Found {len(projects)} matching projects.")
    except Exception as e:
        print(f"Error fetching projects: {e}")
        return

    MAX_GOALS = 10

    for project in projects:
        project_name = project.get("msdyn_subject", "Unnamed Project")
        project_id = project["msdyn_projectid"]
        print(f"\nProcessing project: {project_name} ({project_id})")
        
        try:
            print("  Checking existing goals...")
            existing_count = fetch_existing_goals_count(token, project_id)
            print(f"  Project has {existing_count} existing goals.")
            
            remaining_slots = MAX_GOALS - existing_count
            if remaining_slots <= 0:
                print(f"  [SKIPPING] Project already reached the limit of {MAX_GOALS} goals.")
                continue
            
            goals_to_add = GOALS_TO_ADD[:remaining_slots]
            if len(goals_to_add) < len(GOALS_TO_ADD):
                print(f"  [WARNING] Only adding {len(goals_to_add)} goals to stay within the limit of {MAX_GOALS}.")
            
            print("  Opening Operation Set...")
            op_set_id = create_operation_set(token, project_id)
            
            all_queued = True
            for goal_name in goals_to_add:
                if not add_goal_to_operation_set(token, op_set_id, project_id, goal_name):
                    all_queued = False
            
            if all_queued:
                print("  Committing changes...")
                execute_operation_set(token, op_set_id)
            else:
                print("  [WARNING] Some operations failed to queue. Abandoning Operation Set.")
                abandon_operation_set(token, op_set_id)
            
        except Exception as e:
            print(f"  [ERROR] Failed to process project: {e}")

    print("\nBatch update complete.")

if __name__ == "__main__":
    main()
