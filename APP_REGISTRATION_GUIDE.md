# Azure AD App Registration Guide for Project Goals Script

This guide explains how to set up the necessary Azure AD (Microsoft Entra ID) App Registration to run the `batch_add_goals.py` script using **Interactive Authentication**.

## 1. Create the Registration
1.  Go to the [Azure Portal](https://portal.azure.com).
2.  Navigate to **Microsoft Entra ID** > **App registrations**.
3.  Click **New registration**.
4.  **Name**: `Project Goals Batch Script` (or similar).
5.  **Supported account types**: "Accounts in this organizational directory only" (Single tenant).
6.  **Redirect URI**: Leave blank for now.
7.  Click **Register**.

## 2. Configure Authentication (Public Client)
Since the script uses interactive login, it must be configured as a Public Client.
1.  In the app registration menu, select **Authentication**.
2.  Click **+ Add a platform** and select **Mobile and desktop applications**.
3.  In the "Configure Desktop + Devices" pane, check the box for `http://localhost`.
4.  Click **Save**.

## 3. Add API Permissions
The script needs permission to access Dataverse on your behalf.
1.  In the menu, select **API permissions**.
2.  Click **+ Add a permission**.
3.  Select **Dynamics CRM** (often listed under "APIs my organization uses").
4.  Select **Delegated permissions**.
5.  Check the box for **user_impersonation**.
6.  Click **Add permissions**.
7.  **Admin Consent**: Click **Grant admin consent for HEMY AS** so that you (and others) are not prompted for consent on every run.

## 4. Final Configuration
From the **Overview** page, copy the following values into your `.env` file:

- **Application (client) ID** -> `CLIENT_ID`
- **Directory (tenant) ID** -> `TENANT_ID`

### Example `.env` file:
```env
DATAVERSE_URL=https://yourorg.crm.dynamics.com
TENANT_ID=00000000-0000-0000-0000-000000000000
CLIENT_ID=00000000-0000-0000-0000-000000000000
```
*(No Client Secret is required for interactive login.)*
