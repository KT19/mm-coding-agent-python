import os
from pathlib import Path

# ABSOLUTE boundary for the workspace
WORKSPACE_ROOT = Path(os.getcwd()) / "workspace"


def _is_safe_path(target_path: str) -> bool:
    """Internal helper to prevent path traversal attacks outside the workspace."""
    try:
        resolved_target = Path(WORKSPACE_ROOT / target_path).resolve()
        return WORKSPACE_ROOT in resolved_target.parents or resolved_target == WORKSPACE_ROOT
    except Exception:
        return False


def make_workspace_directory(dir_path: str) -> str:
    """
    Creates a new directory or nested directories within the workspace boundary.
    Use this to structure your codebase logically (e.g., "src/utils", "tests").

    Args:
        dir_path (str): The relative path of the directory structure to create.
    """
    if not _is_safe_path(dir_path):
        return f"Error: Attempted to create directory outside workspace: {dir_path}"

    try:
        target_dir = Path(WORKSPACE_ROOT / dir_path).resolve()
        target_dir.mkdir(parents=True, exist_ok=True)
        return f"Success: Created directory '{target_dir}' (including any nested parents)."
    except Exception as e:
        return f"Error: Failed to create directory '{dir_path}': {str(e)}"


def write_workspace_file(filename: str, content: str) -> str:
    """
    Writes or overwrites text content to a specific file within the workspace.
    Supports nested paths (folders must be created via make_workspace_directory first).

    CRITICAL RULE FOR PYTHON THIRD-PARTY DEPENDENCIES:
    If the code you are writing requires ANY external third-party libraries
    (e.g., requests, beautifulsoup4, matplotlib, pillow), you MUST declare them
    at the absolute top of the 'content' string using a PEP 723 inline script metadata block.
     Do not add this block if you are only importing standard library modules.

    EXAMPLE CONTENT FORMAT WITH EXTERNAL LIBRARIES:
    # /// script
    # dependencies = [
    #   "requests",
    #   "matplotlib"
    # ]
    # ///
    import requests
    import matplotlib.pyplot as plt
    # Your code continues below...

    Args:
        filename (str): The relative path of the target file (e.g., 'src/core/analytics.py').
        content (str): The exact, raw string content or complete source code to write into the file.
    """
    if not _is_safe_path(filename):
        return f"Error: Attempted to write outside workspace: {filename}"

    try:
        target_file = (WORKSPACE_ROOT / filename).resolve()

        if not target_file.parent.exists():
            return f"Error: Directory '{target_file.parent.relative_to(WORKSPACE_ROOT)}' does not exist. Please call 'make_worksapce_directory' with the correct path first."

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: Written {len(content)} characters to '{filename}'."
    except Exception as e:
        return f"Error: Failed to write file due to {str(e)}"


def read_workspace_file(filename: str) -> str:
    """
    Reads and returns the full text content of an existing file in the workspace.
    Use this to inspect code before modifying or debbuging it.

    Args:
        filename (str): The name of the file to read (e.g., "app.py")

    Returns:
        str: The raw content of the file or an error message.
    """
    if not _is_safe_path(filename):
        return f"Error: Attempted to read outside workspace: {filename}"

    try:
        target_file = (WORKSPACE_ROOT / filename).resolve()

        if not target_file.exists() or not target_file.is_file():
            return f"Error: File '{filename}' does not exist in the workspace."

        with open(target_file, "r", encoding="utf-8") as f:
            return f"---Content of '{filename}'---\n{f.read()}"
    except Exception as e:
        return f"Error: Failed to read file '{filename}': {str(e)}"


def list_workspace_files() -> str:
    """
    Recursively maps out the entire workspace layout using a scannable tree format.
    Automatically filters out standard dependency noise (e.g. node_modules, .git)

    Returns:
        str: A formatted list of files found in the workspace root.
    """
    ignored_patterns = ["__pycache__", ".git", "node_modules", ".venv", ".DS_Store"]
    tree_lines = ["--- Workspace Architecture Tree ---", "workspace/"]

    def _build_tree(current_dir: Path, prefix: str = "") -> None:
        try:
            # Sort items to keep terminal print output completely stable and deterministic
            items = sorted(list(current_dir.iterdir()), key=lambda x: (x.is_file(), x.name))
            # Filter out ignored patterns
            visible_items = [item for item in items if item.name not in ignored_patterns]

            for index, item in enumerate(visible_items):
                is_last = index == len(visible_items) - 1
                connector = "└─ " if is_last else "├─ "

                tree_lines.append(f"{prefix}{connector}{item.name}")

                if item.is_dir():
                    extension_prefix = "    " if is_last else "│   "
                    _build_tree(item, prefix + extension_prefix)

        except Exception as e:
            tree_lines.append(f"{prefix}└─ [Error mapping subdirectory: {str(e)}]")

    _build_tree(WORKSPACE_ROOT)
    return "\n".join(tree_lines)
