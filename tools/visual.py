import os
from pathlib import Path


def inspect_image_workspace(filename: str) -> str:
    """
    Prepares a local workspace image (e.g., charts, plots, rendered UI screens)
    for the agent's internal vision processing systems to inspect layout and correctness.

    Args:
        filename (str): The name of the image file to inspect (e.g., 'chart.png')

    Returns:
        str: A systemic acknowledgment status read by the orchestration loop.
    """
    # Prevent Directory Traversal Vulnerabilities by resolving path within workspace
    workspace_root = os.path.join(os.getcwd(), "workspace")
    try:
        resolved_path = Path(workspace_root) / filename
        resolved_path = resolved_path.resolve()

        # Ensure resolved path is inside the workspace directory
        if not (
            Path(workspace_root) in resolved_path.parents or resolved_path == Path(workspace_root)
        ):
            return f"Error: Attempted directory traversal outside workspace: {filename}"
    except Exception as e:
        return f"Error: Invalid image path '{filename}': {str(e)}"

    if not resolved_path.exists():
        return f"Error: Image asset '{filename}' could not be located in the workspace."

    return f"__ATTACH_IMAGE_SIGNAL__:{resolved_path}"
