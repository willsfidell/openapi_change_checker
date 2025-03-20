import importlib.util
import os
import sys
import tempfile
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

        path_to_load = app_path or self.app_path
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

        # Get the app file from the base branch
        base_app_content = reporter.get_base_branch_file(
            str(self.app_path.relative_to(Path.cwd()))
        )
        if not base_app_content:
            return None

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            tmp.write(base_app_content)
            tmp_path = Path(tmp.name)

        try:
            # Load the app and get spec
            app = self._load_fastapi_app(tmp_path)
            spec = app.openapi()

            if not self.validate_spec(spec):
                return None

            return spec
        except Exception:
            return None
        finally:
            # Clean up temporary file
            os.unlink(tmp_path)
