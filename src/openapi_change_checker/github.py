import os
from typing import Optional
import subprocess

from github import Github
from github.PullRequest import PullRequest


class GitHubPRReporter:
    """Handle GitHub PR interactions for reporting changes."""

    def __init__(self, token: str, repo_name: str):
        self.gh = Github(token)
        self.repo = self.gh.get_repo(repo_name)
        self.token = token

    def post_report(self, pr_number: int, report: str) -> None:

        try:
            pr = self.repo.get_pull(pr_number)
            self._update_or_create_comment(pr, report)
        except Exception as e:
            raise ValueError(f"Error posting to PR #{pr_number}: {e}")

    def _update_or_create_comment(self, pr: PullRequest, report: str) -> None:

        # Look for existing report comment
        existing_comment = None
        for comment in pr.get_issue_comments():
            if comment.body.startswith("# OpenAPI Specification Changes"):
                existing_comment = comment
                break

        if existing_comment:
            existing_comment.edit(report)
        else:
            pr.create_issue_comment(report)


    def checkout_base_branch(self, target_dir: str) -> None:
        """Check out the base branch into the specified directory.
        
        Args:
            target_dir: Directory where the base branch should be checked out
        """
        try:
            # Get the clone URL with authentication
            clone_url = self.repo.clone_url.replace(
                "https://", f"https://{self.token}@"
            )
            
            # Get the default branch name
            default_branch = self.repo.default_branch
            print(f"Default: {default_branch}")
            
            # Clone the repository and checkout the base branch
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", default_branch, clone_url, target_dir],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Error checking out base branch: {e.stderr.decode()}")
        except Exception as e:
            raise ValueError(f"Error checking out base branch: {e}")
