import os
import shutil
import subprocess
from pathlib import Path

from tools.file_system import WORKSPACE_ROOT


def _resolve_uv_binary() -> str:
    """
    Dynamically tracks down the absolute system path to the 'uv' executable.
    """
    # Check if 'uv' is explicitly accessible in the current environment PATH
    discovered_path = shutil.which("uv")
    if discovered_path:
        return discovered_path

    # Fall back to common standalone installation
    home_dir = Path.home()
    structural_fallbacks = [
        home_dir / ".local" / "bin" / "uv",
        home_dir / ".local" / "bin" / "uv.exe",
    ]

    for path in structural_fallbacks:
        if path.exists():
            return str(path)

    raise RuntimeError(
        "Could not locate the 'uv' binary on the system.\n"
        "Please install uv or update this tool to match your installation path."
    )


def execute_python_script(filename: str, timeout_seconds: int = 60) -> str:
    """
    Safely executes a Python script present in the local workspace directory using 'uv' execution engine.
    Automatically provisions inline dependencies defined via PEP 723 script blocks.
    Captures standard output, runtime errors, exit codes, and handles infinite loops.
    The program is executed like 'uv run <filename>'. So, you don't need to use 'python' command.

    Args:
        filename (str): The name of the script file to run (e.g., 'app.py'.)
        timeout_seconds (int): Maximum allowed execution time in seconds before halting.

    Returns:
        str: A comprehensive terminal report detailing stdout, stderr, or timeout alerts.
    """
    # Prevent directory traversal while preserving valid nested workspace paths.
    resolved_path = Path(WORKSPACE_ROOT / filename).resolve()

    if not (WORKSPACE_ROOT in resolved_path.parents or resolved_path == WORKSPACE_ROOT):
        return f"Error: Attempted to access file outside workspace: {filename}"

    # Verify script exists before attempting execution
    if not resolved_path.exists() or not resolved_path.is_file():
        return f"Error: Script '{resolved_path}' does not exist in the workspace."

    try:
        uv_executable = _resolve_uv_binary()
        relative_script_path = resolved_path.relative_to(WORKSPACE_ROOT)

        print(
            f"[Sandbox] Launching safe process: {uv_executable} {relative_script_path} (Timeout: {timeout_seconds}s)"
        )

        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"

        # Run script in a totally isolated subprocess
        result = subprocess.run(
            [uv_executable, "run", str(relative_script_path)],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
        )

        # Format the execution artifacts into structural logs
        report = []
        report.append(f"--- Execution Report for '{relative_script_path}'")
        report.append(f"Exit Code: {result.returncode}")

        if result.stdout:
            report.append(f"\n[Standard Output]:\n{result.stdout.strip()}")
        if result.stderr:
            report.append(f"\n[Standard Error / Stack Trace]:\n{result.stderr.strip()}")

        if not result.stdout and not result.stderr:
            report.append("\n[System Notice]: Script executed successfully but returned no output.")

        return "\n".join(report)

    # Handle Rogue Code & Infinite Loops Explicitly
    except subprocess.TimeoutExpired:
        return (
            f"Execution Error: Process timed out after {timeout_seconds} seconds.\n"
            f"Possible causes: Infinite loop, unresolved input prompts, or intensive background operations. "
            f"Please review and optimize your logic."
        )

    except Exception as e:
        return f"System Execution Critical Failure: {str(e)}"
