import os
from typing import Iterable

from azure.identity import ClientSecretCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import (
    ForecastDefinition, ForecastDataset, ForecastAggregation, ForecastResult
)
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.v2024_11_01.models import ResourceGroup

from mcp_server import mcp

_FORECAST_PARAMS = ForecastDefinition(
    type="Usage",
    timeframe="MonthToDate",
    dataset=ForecastDataset(
        granularity="Monthly",
        aggregation={"totalCost": ForecastAggregation(name="Cost", function="Sum")}
    )
)


def get_azure_credentials():
    """Get Azure credentials from environment variables."""
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")

    if not all([tenant_id, client_id, client_secret]):
        raise ValueError("Please set AZURE_TENANT_ID, AZURE_CLIENT_ID, and AZURE_CLIENT_SECRET.")

    return ClientSecretCredential(tenant_id, client_id, client_secret)


def get_cost_management_client(
        credential: ClientSecretCredential,
        subscription_id: str
) -> CostManagementClient:
    """Get Azure Cost Management client."""
    return CostManagementClient(credential=credential, subscription_id=subscription_id)


def get_resource_management_client(
        credential: ClientSecretCredential,
        subscription_id: str
) -> ResourceManagementClient:
    """Get Azure Resource Management client."""
    return ResourceManagementClient(credential=credential, subscription_id=subscription_id)


def get_compute_management_client(
        credential: ClientSecretCredential,
        subscription_id: str
) -> ComputeManagementClient:
    """Get Azure Compute Management client."""
    return ComputeManagementClient(credential=credential, subscription_id=subscription_id)


@mcp.tool()
def get_azure_forecast() -> str:
    cred = get_azure_credentials()
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    cost_management_client: CostManagementClient = get_cost_management_client(cred, subscription_id)

    if not subscription_id:
        return "❌ AZURE_SUBSCRIPTION_ID is not set."

    scope = f"/subscriptions/{subscription_id}"

    try:
        result: ForecastResult = cost_management_client.forecast.usage(scope, _FORECAST_PARAMS)
    except Exception as e:
        return f"Could not retrieve forecast. Please check your Azure credentials, {e}."

    response_string = ""
    for row in result.rows:
        response_string += f"{row}\n"

    return response_string


@mcp.tool(
    description="List all Azure resource groups in the current subscription."
)
def get_azure_resource_groups():
    cred = get_azure_credentials()
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    resource_management_client: ResourceManagementClient = get_resource_management_client(cred, subscription_id)

    try:
        resource_groups: Iterable[ResourceGroup] = resource_management_client.resource_groups.list()
    except Exception as e:
        return f"Could not retrieve resource groups. Please check your Azure credentials, {e}."

    response_string: str = ""
    for resource_group in resource_groups:
        response_string += f"{resource_group.name}\n"

    return response_string


@mcp.tool()
def get_azure_virtual_machines():
    cred = get_azure_credentials()
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    compute_management_client: ComputeManagementClient = get_compute_management_client(cred, subscription_id)

    try:
        virtual_machines = compute_management_client.virtual_machines.list_all()
    except Exception as e:
        return f"Could not retrieve virtual machines. Please check your Azure credentials, {e}."

    response_string: str = ""
    for vm in virtual_machines:
        response_string += f"{vm.name}\n"

    return response_string
