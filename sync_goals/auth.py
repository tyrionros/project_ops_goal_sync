from msal import PublicClientApplication
from . import config

def get_access_token():
    authority = f"https://login.microsoftonline.com/{config.TENANT_ID}"
    app = PublicClientApplication(config.CLIENT_ID, authority=authority)
    
    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(scopes=[f"{config.DATAVERSE_URL}/.default"], account=accounts[0])
    
    if not result:
        print("Opening browser for interactive login...")
        result = app.acquire_token_interactive(scopes=[f"{config.DATAVERSE_URL}/.default"])
    
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception(f"Could not acquire token: {result.get('error_description')}")
