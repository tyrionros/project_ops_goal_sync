import requests
import json
import uuid
from . import config

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8"
    }

def fetch_projects(token):
    url = f"{config.DATAVERSE_URL}/api/data/{config.API_VERSION}/msdyn_projects?$filter={config.PROJECT_FILTER}&$select=msdyn_projectid,msdyn_subject"
    response = requests.get(url, headers=get_headers(token))
    response.raise_for_status()
    return response.json()["value"]

def fetch_existing_goals(token, project_id):
    url = f"{config.DATAVERSE_URL}/api/data/{config.API_VERSION}/msdyn_projectgoals?$filter=_msdyn_projectid_value eq {project_id}&$select=msdyn_projectgoalid,msdyn_name"
    response = requests.get(url, headers=get_headers(token))
    response.raise_for_status()
    return response.json().get("value", [])

def create_operation_set(token, project_id):
    url = f"{config.DATAVERSE_URL}/api/data/{config.API_VERSION}/msdyn_CreateOperationSetV1"
    payload = {"msdyn_projectid": project_id, "msdyn_description": "Modular Sync Goals Script"}
    response = requests.post(url, headers=get_headers(token), json=payload)
    if response.status_code != 200:
        payload = {"ProjectId": project_id, "Description": "Modular Sync Goals Script"}
        response = requests.post(url, headers=get_headers(token), json=payload)
    response.raise_for_status()
    return response.json()["OperationSetId"]

def update_goal_in_operation_set(token, operation_set_id, goal_id, new_name):
    url = f"{config.DATAVERSE_URL}/api/data/{config.API_VERSION}/msdyn_PssUpdateV1"
    entity_data = {
        "@odata.type": "Microsoft.Dynamics.CRM.msdyn_projectgoal",
        "msdyn_projectgoalid": goal_id,
        "msdyn_name": new_name
    }
    payload = {"Entity": entity_data, "OperationSetId": operation_set_id}
    response = requests.post(url, headers=get_headers(token), json=payload)
    if response.status_code not in [200, 204]:
        payload["Entity"] = json.dumps(entity_data)
        response = requests.post(url, headers=get_headers(token), json=payload)
    
    if response.status_code not in [200, 204]:
        print(f"    [ERROR] Update failed for '{new_name}': {response.text}")
        return False
    return True

def create_goal_in_operation_set(token, operation_set_id, project_id, goal_name):
    url = f"{config.DATAVERSE_URL}/api/data/{config.API_VERSION}/msdyn_PssCreateV1"
    goal_id = str(uuid.uuid4())
    entity_data = {
        "@odata.type": "Microsoft.Dynamics.CRM.msdyn_projectgoal",
        "msdyn_projectgoalid": goal_id,
        "msdyn_name": goal_name,
        "msdyn_projectid@odata.bind": f"/msdyn_projects({project_id})"
    }
    payload = {"Entity": entity_data, "OperationSetId": operation_set_id}
    response = requests.post(url, headers=get_headers(token), json=payload)
    if response.status_code not in [200, 204]:
        payload["Entity"] = json.dumps(entity_data)
        response = requests.post(url, headers=get_headers(token), json=payload)

    if response.status_code not in [200, 204]:
        print(f"    [ERROR] Create failed for '{goal_name}': {response.text}")
        return False
    return True

def delete_goal_from_operation_set(token, operation_set_id, goal_id, goal_name):
    url = f"{config.DATAVERSE_URL}/api/data/{config.API_VERSION}/msdyn_PssDeleteV1"
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
    url = f"{config.DATAVERSE_URL}/api/data/{config.API_VERSION}/msdyn_ExecuteOperationSetV1"
    response = requests.post(url, headers=get_headers(token), json={"OperationSetId": operation_set_id})
    response.raise_for_status()

def abandon_operation_set(token, operation_set_id):
    url = f"{config.DATAVERSE_URL}/api/data/{config.API_VERSION}/msdyn_AbandonOperationSetV1"
    requests.post(url, headers=get_headers(token), json={"OperationSetId": operation_set_id})
