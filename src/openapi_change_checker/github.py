from typing import Optional

from github import Github
from github.PullRequest import PullRequest


class GitHubPRReporter:
    """Handle GitHub PR interactions for reporting changes."""

    def __init__(self, token: str, repo_name: str):
        self.gh = Github(token)
        self.repo = self.gh.get_repo(repo_name)

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

    def get_base_branch_file(self, path: str) -> Optional[str]:
        try:
            content = self.repo.get_contents(path)
            return content.decoded_content.decode("utf-8")
        except Exception:
            return None
