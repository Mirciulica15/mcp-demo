from dotenv import load_dotenv

from tools.azure import *


def test_get_azure_forecast():
    """
    Test the get_azure_forecast function.
    """
    result = get_azure_forecast()
    assert isinstance(result, str), "Expected a string response"
    assert "forecast" in result.lower(), "Expected forecast data in the response"
    print("Result", result)


def test_get_azure_resource_groups():
    """
    Test the get_azure_resource_groups function.
    """
    result = get_azure_resource_groups()
    assert len(result) > 0, "Expected at least one resource group in the response"
    print("Result", result)


def test_get_azure_virtual_machines():
    """
    Test the get_azure_virtual_machines function.
    """
    result = get_azure_virtual_machines()
    assert isinstance(result, str), "Expected a string response"
    print("Result", result)


if __name__ == "__main__":
    load_dotenv()
    test_get_azure_forecast()
    test_get_azure_resource_groups()
    test_get_azure_virtual_machines()
