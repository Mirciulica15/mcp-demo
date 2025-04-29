from dotenv import load_dotenv

from tools.proxmox import get_proxmox_virtual_machines, get_proxmox_nodes, get_proxmox_users, \
    start_proxmox_virtual_machine, stop_proxmox_virtual_machine


def test_get_proxmox_virtual_machines():
    """
    Test the get_proxmox_virtual_machine function.
    """
    result = get_proxmox_virtual_machines()
    # assert isinstance(result, dict), "Expected a dictionary response"
    # assert len(result) > 0, "Expected at least one virtual machine in the response"
    print("Result", result)


def test_get_proxmox_nodes():
    """
    Test the get_proxmox_virtual_machine function.
    """
    result = get_proxmox_nodes()
    # assert isinstance(result, dict), "Expected a dictionary response"
    # assert len(result) > 0, "Expected at least one virtual machine in the response"
    print("Result", result)


def test_get_proxmox_users():
    """
    Test the get_proxmox_virtual_machine function.
    """
    result = get_proxmox_users()
    # assert isinstance(result, dict), "Expected a dictionary response"
    # assert len(result) > 0, "Expected at least one virtual machine in the response"
    print("Result", result)


def test_start_proxmox_virtual_machine():
    """
    Test the start_proxmox_virtual_machine function.
    """
    vm_id = "109"
    result = start_proxmox_virtual_machine(vm_id)
    # assert isinstance(result, str), "Expected a string response"
    print("Result", result)


def test_stop_proxmox_virtual_machine():
    """
    Test the stop_proxmox_virtual_machine function.
    """
    vm_id = "109"
    result = stop_proxmox_virtual_machine(vm_id)
    # assert isinstance(result, str), "Expected a string response"
    print("Result", result)


if __name__ == "__main__":
    load_dotenv()
    test_get_proxmox_virtual_machines()
    test_get_proxmox_nodes()
    test_get_proxmox_users()
    # test_start_proxmox_virtual_machine()
    # test_stop_proxmox_vm()
