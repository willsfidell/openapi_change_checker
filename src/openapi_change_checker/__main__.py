import argparse
import json
import os
import sys
from pathlib import Path

from .comparison import SpecComparison
from .consumers.config import ConsumerConfigLoader
from .consumers.impact import ImpactAnalyzer
from .github import GitHubPRReporter
from .report import MarkdownReport
from .spec_handler import SpecHandler
from .spec_handler.fastapi import FastAPISpecHandler
from .spec_handler.static import StaticSpecHandler


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="OpenAPI Change Checker")
    parser.add_argument("command", choices=["check"], help="Command to execute")
    parser.add_argument(
        "--spec-source",
        choices=["fastapi", "static"],
        required=True,
        help="Source of OpenAPI spec",
    )
    parser.add_argument(
        "--fastapi-app", help="Path to FastAPI app (required if spec_source is fastapi)"
    )
    parser.add_argument(
        "--openapi-file",
        help="Path to static OpenAPI spec file (required if spec_source is static)",
    )
    parser.add_argument(
        "--consumers-config", help="Path to consumers configuration file"
    )
    parser.add_argument("--repo", required=True, help="GitHub repository (owner/repo)")
    parser.add_argument("--pr", type=int, required=True, help="Pull request number")

    args = parser.parse_args()

    # Validate arguments
    if args.spec_source == "fastapi" and not args.fastapi_app:
        parser.error("--fastapi-app is required when spec_source is fastapi")
    if args.spec_source == "static" and not args.openapi_file:
        parser.error("--openapi-file is required when spec_source is static")

    return args


def get_spec_handler(args: argparse.Namespace) -> SpecHandler:
    """Create the appropriate spec handler based on arguments."""
    if args.spec_source == "fastapi":
        return FastAPISpecHandler(
            app_path=args.fastapi_app,
            github_token=os.environ["GITHUB_TOKEN"],
            repo_name=args.repo,
        )
    else:
        return StaticSpecHandler(
            file_path=args.openapi_file,
            github_token=os.environ["GITHUB_TOKEN"],
            repo_name=args.repo,
        )


def main() -> int:
    """Main entry point."""
    try:
        args = parse_args()

        if args.command == "check":
            # Get spec handler
            handler = get_spec_handler(args)

            # Get current and previous specs
            current_spec = handler.get_current_spec()
            previous_spec = handler.get_previous_spec(args.pr)

            if not previous_spec:
                print("No previous spec found for comparison")
                return 0

            # Compare specs
            comparison = SpecComparison(current_spec, previous_spec)

            # Load consumer configs if provided
            consumer_impacts = None
            if args.consumers_config:
                consumers = ConsumerConfigLoader.load_from_file(
                    Path(args.consumers_config)
                )
                analyzer = ImpactAnalyzer(comparison, consumers)
                consumer_impacts = analyzer.analyze_consumer_impacts()

            # Generate report
            report = MarkdownReport(comparison, consumer_impacts)
            report_content = report.generate()

            # Post to PR
            reporter = GitHubPRReporter(
                token=os.environ["GITHUB_TOKEN"], repo_name=args.repo
            )
            reporter.post_report(args.pr, report_content)

            # Store current spec if using FastAPI
            if args.spec_source == "fastapi":
                handler.store_spec(current_spec)

            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
