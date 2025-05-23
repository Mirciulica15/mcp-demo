from tools.kubernetes import get_pods_api, create_demo_nginx


def test_get_pods_in_all_namespaces():
    pods = get_pods_api()
    assert pods is not None, "Failed to retrieve pods"


def test_create_demo_nginx():
    result = create_demo_nginx()
    assert "Nginx demo is up!" in result, "Failed to create Nginx demo"
    print("Result:", result)


if __name__ == "__main__":
    test_get_pods_in_all_namespaces()
    test_create_demo_nginx()
