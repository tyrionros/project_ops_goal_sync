import os
import requests
import uuid
import json
from msal import PublicClientApplication
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATAVERSE_URL = os.getenv("DATAVERSE_URL")
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")

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
PROJECT_FILTER = "contains(msdyn_subject, 'IAM Test')"

def get_access_token():
    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = PublicClientApplication(CLIENT_ID, authority=authority)
    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(scopes=[f"{DATAVERSE_URL}/.default"], account=accounts[0])
    if not result:
        print("Opening browser for interactive login...")
        result = app.acquire_token_interactive(scopes=[f"{DATAVERSE_URL}/.default"])
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Could not acquire token: {result.get('error_description')}")

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8"
    }

def fetch_projects(token):
    url = f"{DATAVERSE_URL}/api/data/{API_VERSION}/msdyn_projects?$filter={PROJECT_FILTER}&$select=msdyn_projectid,msdyn_subject"
    response = requests.get(url, headers=get_headers(token))
    response.raise_for_status()
    return response.json()["value"]

def fetch_existing_goals(token, project_id):
    url = f"{DATAVERSE_URL}/api/data/{API_VERSION}/msdyn_projectgoals?$filter=_msdyn_projectid_value eq {project_id}&$select=msdyn_projectgoalid,msdyn_name"
    response = requests.get(url, headers=get_headers(token))
    response.raise_for_status()
    return response.json().get("value", [])

def create_operation_set(token, project_id):
    url = f"{DATAVERSE_URL}/api/data/{API_VERSION}/msdyn_CreateOperationSetV1"
    payload = {"msdyn_projectid": project_id, "msdyn_description": "Sync Goals Script"}
    response = requests.post(url, headers=get_headers(token), json=payload)
    if response.status_code != 200:
        payload = {"ProjectId": project_id, "Description": "Sync Goals Script"}
        response = requests.post(url, headers=get_headers(token), json=payload)
    response.raise_for_status()
    return response.json()["OperationSetId"]

def update_goal_in_operation_set(token, operation_set_id, goal_id, new_name):
    url = f"{DATAVERSE_URL}/api/data/{API_VERSION}/msdyn_PssUpdateV1"
    entity_data = {
        "@odata.type": "Microsoft.Dynamics.CRM.msdyn_projectgoal",
        "msdyn_projectgoalid": goal_id,
        "msdyn_name": new_name
    }
    # IMPORTANT: Passing Entity as an object, not stringified JSON
    payload = {"Entity": entity_data, "OperationSetId": operation_set_id}
    response = requests.post(url, headers=get_headers(token), json=payload)
    if response.status_code not in [200, 204]:
        # Fallback to stringified if object fails
        payload["Entity"] = json.dumps(entity_data)
        response = requests.post(url, headers=get_headers(token), json=payload)
    
    if response.status_code not in [200, 204]:
        print(f"    [ERROR] Update failed for '{new_name}': {response.text}")
        return False
    return True

def create_goal_in_operation_set(token, operation_set_id, project_id, goal_name):
    url = f"{DATAVERSE_URL}/api/data/{API_VERSION}/msdyn_PssCreateV1"
    goal_id = str(uuid.uuid4())
    entity_data = {
        "@odata.type": "Microsoft.Dynamics.CRM.msdyn_projectgoal",
        "msdyn_projectgoalid": goal_id,
        "msdyn_name": goal_name,
        "msdyn_projectid@odata.bind": f"/msdyn_projects({project_id})"
    }
    # IMPORTANT: Passing Entity as an object, not stringified JSON
    payload = {"Entity": entity_data, "OperationSetId": operation_set_id}
    response = requests.post(url, headers=get_headers(token), json=payload)
    if response.status_code not in [200, 204]:
        # Fallback to stringified if object fails
        payload["Entity"] = json.dumps(entity_data)
        response = requests.post(url, headers=get_headers(token), json=payload)

    if response.status_code not in [200, 204]:
        print(f"    [ERROR] Create failed for '{goal_name}': {response.text}")
        return False
    return True

def delete_goal_from_operation_set(token, operation_set_id, goal_id, goal_name):
    url = f"{DATAVERSE_URL}/api/data/{API_VERSION}/msdyn_PssDeleteV1"
    payload = {
        "EntityName": "msdyn_projectgoal",
        "RecordId": goal_id,
        "OperationSetId": operation_set_id
    }
    response = requests.post(url, headers=get_headers(token), json=payload)
    if response.status_code not in [200, 204]:
        print(f"    [ERROR] Delete failed for '{goal_name}': {response.text}")
        return False
    return True

def execute_operation_set(token, operation_set_id):
    url = f"{DATAVERSE_URL}/api/data/{API_VERSION}/msdyn_ExecuteOperationSetV1"
    response = requests.post(url, headers=get_headers(token), json={"OperationSetId": operation_set_id})
    response.raise_for_status()

def abandon_operation_set(token, operation_set_id):
    url = f"{DATAVERSE_URL}/api/data/{API_VERSION}/msdyn_AbandonOperationSetV1"
    requests.post(url, headers=get_headers(token), json={"OperationSetId": operation_set_id})

def main():
    if not all([DATAVERSE_URL, TENANT_ID, CLIENT_ID]):
        print("Error: Missing environment variables.")
        return

    print("--- STARTING GOAL SYNCHRONIZATION (RENAME/CREATE/DELETE) ---")
    token = get_access_token()
    projects = fetch_projects(token)
    print(f"Found {len(projects)} matching projects.")

    for project in projects:
        project_name = project.get("msdyn_subject", "Unnamed Project")
        project_id = project["msdyn_projectid"]
        print(f"\nProcessing project: {project_name}")
        
        op_set_id = None
        try:
            existing_goals = fetch_existing_goals(token, project_id)
            print(f"  Project has {len(existing_goals)} existing goals.")
            
            op_set_id = create_operation_set(token, project_id)
            all_queued = True
            
            num_to_update = min(len(existing_goals), len(GOALS_TO_ADD))
            
            # Step 1: Update (Rename)
            for i in range(num_to_update):
                goal = existing_goals[i]
                new_name = GOALS_TO_ADD[i]
                if update_goal_in_operation_set(token, op_set_id, goal["msdyn_projectgoalid"], new_name):
                    print(f"    [UPDATE QUEUED] '{goal['msdyn_name']}' -> '{new_name}'")
                else:
                    all_queued = False

            # Step 2: Create
            if len(GOALS_TO_ADD) > len(existing_goals):
                for i in range(num_to_update, len(GOALS_TO_ADD)):
                    new_name = GOALS_TO_ADD[i]
                    if create_goal_in_operation_set(token, op_set_id, project_id, new_name):
                        print(f"    [CREATE QUEUED] '{new_name}'")
                    else:
                        all_queued = False
            
            # Step 3: Delete
            if len(existing_goals) > len(GOALS_TO_ADD):
                for i in range(num_to_update, len(existing_goals)):
                    goal = existing_goals[i]
                    if delete_goal_from_operation_set(token, op_set_id, goal["msdyn_projectgoalid"], goal["msdyn_name"]):
                        print(f"    [DELETE QUEUED] '{goal['msdyn_name']}'")
                    else:
                        all_queued = False
            
            if all_queued:
                print("  Executing synchronization batch...")
                execute_operation_set(token, op_set_id)
                print("  [SUCCESS] Synchronization triggered.")
            else:
                print("  [ERROR] Some operations failed to queue. Abandoning batch.")
                abandon_operation_set(token, op_set_id)
                
        except Exception as e:
            print(f"  [ERROR] Failed project {project_name}: {e}")
            if op_set_id:
                abandon_operation_set(token, op_set_id)

    print("\nSynchronization complete.")

if __name__ == "__main__":
    main()
