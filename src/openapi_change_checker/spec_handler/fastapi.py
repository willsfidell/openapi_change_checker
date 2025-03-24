import importlib.util
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Optional

from ..github import GitHubPRReporter
from . import SpecHandler


class FastAPISpecHandler(SpecHandler):
    """Handler for FastAPI-generated OpenAPI specifications."""

    def __init__(
        self,
        app_path: str,
        github_token: str,
        repo_name: str,
    ):

        self.app_path = Path(app_path)
        self.github_token = github_token
        self.repo_name = repo_name

        if not self.app_path.exists():
            raise FileNotFoundError(f"FastAPI app not found: {app_path}")

    def _load_fastapi_app(self, app_path: Optional[Path] = None):

        print(app_path)
        path_to_load = app_path or self.app_path
        print(path_to_load)
        try:
            # Add the app's directory to sys.path
            sys.path.insert(0, str(path_to_load.parent))

            # Import the module
            spec = importlib.util.spec_from_file_location(
                "fastapi_app", str(path_to_load)
            )
            if spec is None or spec.loader is None:
                raise ImportError("Could not load FastAPI app specification")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find the FastAPI instance
            from fastapi import FastAPI

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, FastAPI):
                    return attr

            raise ImportError("No FastAPI instance found in module")
        finally:
            # Remove the added path
            sys.path.pop(0)

    def get_current_spec(self) -> Dict:

        app = self._load_fastapi_app()
        spec = app.openapi()

        if not self.validate_spec(spec):
            raise ValueError("Invalid OpenAPI specification generated")

        return spec

    def get_previous_spec(self, pr_number: int) -> Optional[Dict]:

        reporter = GitHubPRReporter(self.github_token, self.repo_name)

        try:
            # Create a temporary directory with UUID
            temp_dir = Path(tempfile.gettempdir()) / f"fastapi-spec-{uuid.uuid4()}"
            temp_dir.mkdir(exist_ok=True)

            # Check out the complete base branch into the temp directory
            reporter.checkout_base_branch(str(temp_dir))

            # Construct the full path in the temp directory
            temp_app_path = temp_dir / self.app_path
            print(f"{temp_app_path}")

            if not temp_app_path.exists():
                return None

            # Load the app and get spec
            app = self._load_fastapi_app(temp_app_path)
            spec = app.openapi()
            print(spec)

            if not self.validate_spec(spec):
                return None

            return spec
        except Exception as e:
            print(f"Error getting previous spec: {e}")
            return None
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
