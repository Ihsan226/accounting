#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import pathlib
import subprocess


def main():
    """Run administrative tasks."""
    # Ensure we run with the project's virtualenv Python on Windows.
    # If current interpreter isn't the venv one, re-exec using env\Scripts\python.exe.
    try:
        project_root = pathlib.Path(__file__).resolve().parent
        venv_python = project_root / 'env' / 'Scripts' / 'python.exe'
        current = pathlib.Path(sys.executable)
        if venv_python.exists() and current != venv_python:
            # Relaunch this command with venv python and same args.
            subprocess.run([str(venv_python), str(pathlib.Path(__file__).resolve())] + sys.argv[1:])
            return
    except Exception:
        # If anything goes wrong, continue with current interpreter.
        pass

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'akutansi_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
