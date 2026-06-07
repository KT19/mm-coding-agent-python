from tools.file_system import (
    list_workspace_files,
    make_workspace_directory,
    read_workspace_file,
    write_workspace_file,
)
from tools.sandbox import execute_python_script
from tools.visual import inspect_image_workspace

ALLOCATED_TOOLS = {
    "write_workspace_file": write_workspace_file,
    "read_workspace_file": read_workspace_file,
    "list_workspace_files": list_workspace_files,
    "make_workspace_directory": make_workspace_directory,
    "execute_python_script": execute_python_script,
    "inspect_image_workspace": inspect_image_workspace,
}


TOOL_MANIFEST = [
    write_workspace_file,
    read_workspace_file,
    list_workspace_files,
    make_workspace_directory,
    execute_python_script,
    inspect_image_workspace,
]
