from tools.kubernetes import get_pods_api


def test_get_pods_in_all_namespaces():
    pods = get_pods_api()
    assert pods is not None, "Failed to retrieve pods"


if __name__ == "__main__":
    test_get_pods_in_all_namespaces()
