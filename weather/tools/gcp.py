import os
from typing import List, Union, Dict

from google.cloud.billing import CloudBillingClient
from google.cloud.billing.budgets import BudgetServiceClient
from google.cloud.billing_v1 import ProjectBillingInfo
from google.oauth2 import service_account
from googleapiclient import discovery

from mcp_server import mcp


def enable_api_via_discovery(api_service: str):
    """
    Enables the given API (e.g. "cloudbilling.googleapis.com" or "billingbudgets.googleapis.com")
    for the specified GCP project.
    """
    creds = _get_gcp_credentials()
    svc = discovery.build("serviceusage", "v1", credentials=creds)
    name = f"projects/{os.getenv("GCP_PROJECT_ID")}/services/{api_service}"
    resp = svc.services().enable(name=name).execute()
    print(f"Enabled {api_service} → operation: {resp.get('name')}")
    return resp


def _get_gcp_credentials():
    keyfile = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not keyfile:
        raise ValueError("Please set GOOGLE_APPLICATION_CREDENTIALS to your service account JSON path.")
    return service_account.Credentials.from_service_account_file(keyfile)


@mcp.tool(description="List all GCP Cloud Billing account IDs accessible by this service account.")
def get_gcp_billing_accounts() -> List[str]:
    creds = _get_gcp_credentials()
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        return {"error": "Please set GCP_PROJECT_ID"}

    client = CloudBillingClient(credentials=creds)
    try:
        info: ProjectBillingInfo = client.get_project_billing_info(name=f"projects/{project_id}")
    except Exception as e:
        return {"error": str(e)}

    return {
        "project": project_id,
        "billing_enabled": str(info.billing_enabled),
        "billing_account": info.billing_account_name.split("/")[-1] if info.billing_account_name else ""
    }


@mcp.tool(description="List your GCP Budgets (i.e. your planned/forecast thresholds) for the current project.")
def get_gcp_forecast() -> Union[List[str], Dict[str, str]]:
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        return {"error": "Please set GCP_PROJECT_ID to your GCP project ID."}

    creds = _get_gcp_credentials()

    billing_client = CloudBillingClient(credentials=creds)
    try:
        pb_info = billing_client.get_project_billing_info(name=f"projects/{project_id}")
    except Exception as e:
        return {"error": f"Could not fetch project billing info: {e}"}

    if not pb_info.billing_account_name:
        return {"error": f"Project {project_id} has no billing account attached."}

    billing_acct_id = pb_info.billing_account_name.split("/")[-1]

    budget_client = BudgetServiceClient(credentials=creds)
    parent = f"billingAccounts/{billing_acct_id}"
    try:
        pager = budget_client.list_budgets(parent=parent)
    except Exception as e:
        return {"error": f"Could not list budgets for {parent}: {e}"}

    lines: List[str] = []
    for b in pager:
        display = b.display_name or "<unnamed>"
        amt = "[no fixed amount]"
        if b.amount_spec and b.amount_spec.budget_amount:
            micros = b.amount_spec.budget_amount.fixed_amount.micro_amount
            dollars = micros / 1_000_000
            amt = f"${dollars:,.2f}"
        lines.append(f"{display}: {amt}")

    return lines
