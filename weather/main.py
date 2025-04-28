from dotenv import load_dotenv

load_dotenv()

import importlib
import pkgutil

import tools

from mcp_server import mcp


def _load_tools():
    """
    Walk the tools/ package directory and import every .py module.
    Any new file you drop into tools/ automatically gets picked up.
    """
    for finder, name, ispkg in pkgutil.iter_modules(tools.__path__):
        importlib.import_module(f"{tools.__name__}.{name}")


if __name__ == "__main__":
    _load_tools()
    mcp.run(transport="stdio")
