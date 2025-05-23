from dotenv import load_dotenv

from tools.gcp import get_gcp_billing_accounts, get_gcp_forecast


def test_get_gcp_billing_accounts():
    """
    Test the get_gcp_forecast function.
    """

    result = get_gcp_billing_accounts()
    # assert isinstance(result, str), "Expected a string response"
    # assert "forecast" in result.lower(), "Expected forecast data in the response"
    print("Result", result)


def test_get_gcp_forecast():
    """
    Test the get_gcp_forecast function.
    """
    result = get_gcp_forecast()
    # assert isinstance(result, list), "Expected a list response"
    # assert len(result) > 0, "Expected at least one forecast in the response"
    print("Result", result)


if __name__ == "__main__":
    load_dotenv()
    test_get_gcp_billing_accounts()
    test_get_gcp_forecast()
