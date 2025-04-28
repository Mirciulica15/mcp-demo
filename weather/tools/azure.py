import os

from azure.identity import ClientSecretCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import (
    ForecastDefinition, ForecastDataset, ForecastAggregation
)

from mcp_server import mcp

_FORECAST_PARAMS = ForecastDefinition(
    type="Usage",
    timeframe="MonthToDate",
    dataset=ForecastDataset(
        granularity="Daily",
        aggregation={"totalCost": ForecastAggregation(name="Cost", function="Sum")}
    )
)


@mcp.tool()
async def get_azure_forecast() -> str:
    cred = ClientSecretCredential(
        tenant_id=os.getenv("AZURE_TENANT_ID"),
        client_id=os.getenv("AZURE_CLIENT_ID"),
        client_secret=os.getenv("AZURE_CLIENT_SECRET"),
    )

    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    cost_management_client = CostManagementClient(
        cred,
        subscription_id=subscription_id
    )

    if not subscription_id:
        return "❌ AZURE_SUBSCRIPTION_ID is not set."

    scope = f"/subscriptions/{subscription_id}"

    try:
        result = cost_management_client.forecast.usage(scope, _FORECAST_PARAMS)
    except Exception as e:
        return f"Could not retrieve forecast. Please check your Azure credentials, {e}."

    return str(result)
