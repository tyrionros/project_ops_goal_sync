import os
from dotenv import load_dotenv

# Load environment variables from root directory
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

DATAVERSE_URL = os.getenv("DATAVERSE_URL")
TENANT_ID = os.getenv("TENANT_ID")
CLIENT_ID = os.getenv("CLIENT_ID")

# Configuration Constants
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

GOAL_MAPPING = {
    "P53 01 Gather Requirements": "P53 Customer Requirements",
    "P53 02 Development + Documentation": "P53 Development & Technical Documentation in Dev environment",
    "P53 03 Quality Assurance / QA": "P53 Technical QA Testing in UAT environment",
    "P53 04 Release Documentation for End Users": "P53 Functional QA Testing in UAT environment",
    "P53 05 Deployment to Production": "P53 Deployment from Dev to Prod environment",
    "P53 06 Security & IAM Implementation": "P53 Set up IAM in Prod environment"
}