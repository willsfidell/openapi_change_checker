import json
from pathlib import Path
from typing import Dict, Optional

from git import Repo
from git.exc import GitError

from ..github import GitHubPRReporter
from . import SpecHandler


class StaticSpecHandler(SpecHandler):
    """Handler for static OpenAPI specification files."""

    def __init__(self, file_path: str, github_token: str, repo_name: str):

        self.file_path = Path(file_path)
        self.github_token = github_token
        self.repo_name = repo_name

        if not self.file_path.exists():
            raise FileNotFoundError(f"OpenAPI spec file not found: {file_path}")

        try:
            self.repo = Repo(".", search_parent_directories=True)
        except GitError:
            raise RuntimeError("Not a git repository")

    def _read_json_file(self, file_path: Path) -> Dict:

        try:
            with open(file_path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}")

    def get_current_spec(self) -> Dict:

        spec = self._read_json_file(self.file_path)
        if not self.validate_spec(spec):
            raise ValueError("Invalid OpenAPI specification")
        return spec

    def get_previous_spec(self, pr_number: int) -> Optional[Dict]:

        reporter = GitHubPRReporter(self.github_token, self.repo_name)

        # Get the file content from the base branch
        base_content = reporter.get_base_branch_file(
            str(self.file_path.relative_to(Path.cwd()))
        )
        if not base_content:
            return None

        try:
            spec = json.loads(base_content)
            if not self.validate_spec(spec):
                return None
            return spec
        except json.JSONDecodeError:
            return None
