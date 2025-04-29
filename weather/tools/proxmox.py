import os
from typing import List, Iterable

from proxmoxmanager.main import ProxmoxManager
from proxmoxmanager.utils import ProxmoxVM

from mcp_server import mcp


def get_proxmox_manager() -> ProxmoxManager:
    """Get ProxmoxManager instance."""
    proxmox_manager = ProxmoxManager(
        host=os.getenv("PROXMOX_HOST"),
        user=os.getenv("PROXMOX_USER"),
        token_name=os.getenv("PROXMOX_TOKEN_NAME"),
        token_value=os.getenv("PROXMOX_TOKEN_VALUE")
    )
    return proxmox_manager


@mcp.tool()
def get_proxmox_virtual_machines() -> List[str]:
    """
    Return a flat list of all VMIDs across every Proxmox node,
    using only the ProxmoxVMDict/ProxmoxVM SDK classes.
    """
    proxmox_manager = get_proxmox_manager()
    vms: Iterable[ProxmoxVM] = proxmox_manager.vms.values()

    response_string = ""
    for vm in vms:
        response_string += f"Id: {vm.id}, Node: {vm.node}, Running: {vm.running()}\n"
    return response_string


@mcp.tool()
def get_proxmox_nodes():
    proxmox_manager = get_proxmox_manager()
    nodes = proxmox_manager.nodes
    return nodes


@mcp.tool()
def get_proxmox_users():
    proxmox_manager = get_proxmox_manager()
    users = proxmox_manager.users
    return users


@mcp.tool(description="Start a Proxmox virtual machine, given its ID.")
def start_proxmox_virtual_machine(vm_id: str):
    proxmox_manager = get_proxmox_manager()
    vm_is_running: bool = proxmox_manager.vms.__getitem__(vm_id).running()
    if vm_is_running:
        return f"VM {vm_id} is already running."
    proxmox_manager.vms.__getitem__(vm_id).start()


@mcp.tool(description="Stop a Proxmox virtual machine, given its ID.")
def stop_proxmox_virtual_machine(vm_id: str):
    proxmox_manager = get_proxmox_manager()
    vm_is_running: bool = proxmox_manager.vms.__getitem__(vm_id).running()
    if not vm_is_running:
        return f"VM {vm_id} is already stopped."
    proxmox_manager.vms.__getitem__(vm_id).stop()
