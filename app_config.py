import os
from dotenv import load_dotenv
load_dotenv(".env")
CLIENT_ID = os.getenv("CLIENT_ID")

CLIENT_SECRET = os.getenv("CLIENT_SECRET")
# In a production app, we recommend you use a more secure method of storing your secret,
# like Azure Key Vault. Or, use an environment variable as described in Flask's documentation:
# https://flask.palletsprojects.com/en/1.1.x/config/#configuring-from-environment-variables
# CLIENT_SECRET = os.getenv("CLIENT_SECRET")
# if not CLIENT_SECRET:
#     raise ValueError("Need to define CLIENT_SECRET environment variable")

TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"  # For multi-tenant app
# AUTHORITY = "https://login.microsoftonline.com/Enter_the_Tenant_Name_Here"

REDIRECT_PATH = "/get_auth_token"  # Used for forming an absolute URL to your redirect URI.
# The absolute URL must match the redirect URI you set
# in the app's registration in the Azure portal.

# You can find more Microsoft Graph API endpoints from Graph Explorer
# https://developer.microsoft.com/en-us/graph/graph-explorer
ENDPOINT = "https://graph.microsoft.com/v1.0/users"  # This resource requires no admin consent


# You can find the proper permission names from this document
# https://docs.microsoft.com/en-us/graph/permissions-reference
SCOPE = ["User.ReadBasic.All"]

SESSION_TYPE = "filesystem"  # Specifies the token cache should be stored in server-side session
APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
DB_ACCOUNT_URI = os.getenv("DB_ACCOUNT_URI")
DB_ACCOUNT_KEY = os.getenv("DB_ACCOUNT_KEY")
DB_NAME = os.getenv("DB_NAME")
DB_CONTAINER_NAME = os.getenv("DB_CONTAINER_NAME")
PORT = os.getenv("PORT")
VOTING_SERVICE_URL=os.getenv("VOTING_SERVICE_URL")
FUNCTION_KEY=os.getenv("FUNCTION_KEY")