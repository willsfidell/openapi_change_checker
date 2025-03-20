from typing import Dict, List, Optional

from .comparison import SpecComparison
from .consumers.impact import ConsumerImpact, EndpointImpact, ImpactAnalyzer


class MarkdownReport:
    """Generate a markdown report of OpenAPI specification changes."""

    def __init__(
        self,
        comparison: SpecComparison,
        consumer_impacts: Optional[List[ConsumerImpact]] = None,
    ):
        self.comparison = comparison
        self.consumer_impacts = consumer_impacts

    def generate(self) -> str:

        sections = [
            self._generate_header(),
            self._generate_summary(),
            self._generate_changes_section(),
        ]

        if self.consumer_impacts:
            sections.append(self._generate_consumer_impacts())

        return "\n\n".join(sections)

    def _generate_header(self) -> str:
        return "# OpenAPI Specification Changes"

    def _generate_summary(self) -> str:

        new = self.comparison.get_new_endpoints()
        removed = self.comparison.get_removed_endpoints()
        modified = self.comparison.get_modified_endpoints()

        summary = ["## Summary", ""]

        if not (new or removed or modified):
            summary.append("No changes detected in the OpenAPI specification.")
            return "\n".join(summary)

        if new:
            summary.append(
                f"- ✨ Added {len(new)} new endpoint{'s' if len(new) != 1 else ''}"
            )
        if removed:
            summary.append(
                f"- 🗑️ Removed {len(removed)} endpoint{'s' if len(removed) != 1 else ''}"
            )
        if modified:
            summary.append(
                f"- 📝 Modified {len(modified)} endpoint{'s' if len(modified) != 1 else ''}"
            )

        if self.consumer_impacts:
            affected_consumers = [
                impact
                for impact in self.consumer_impacts
                if (
                    impact.breaking_changes
                    or impact.non_breaking_changes
                    or impact.new_endpoints
                    or impact.removed_endpoints
                )
            ]
            if affected_consumers:
                summary.append(f"\n### Affected Consumers")
                for impact in affected_consumers:
                    if impact.has_breaking_changes:
                        symbol = "⚠️"
                    else:
                        symbol = "ℹ️"
                    summary.append(f"- {symbol} {impact.consumer.name}")

        return "\n".join(summary)

    def _generate_changes_section(self) -> str:

        sections = ["## Detailed Changes", ""]

        # New endpoints
        new = self.comparison.get_new_endpoints()
        if new:
            sections.append("### New Endpoints")
            for path in new:
                sections.append(f"- ✨ `{path}`")
            sections.append("")

        # Removed endpoints
        removed = self.comparison.get_removed_endpoints()
        if removed:
            sections.append("### Removed Endpoints")
            for path in removed:
                sections.append(f"- 🗑️ `{path}`")
            sections.append("")

        # Modified endpoints
        modified = self.comparison.get_modified_endpoints()
        if modified:
            sections.append("### Modified Endpoints")
            for path, changes in modified:
                is_breaking = self.comparison.is_breaking_change(path, changes)
                symbol = "⚠️" if is_breaking else "📝"
                sections.append(f"#### {symbol} `{path}`")

                # Group changes by category
                param_changes = {}
                response_changes = {}
                other_changes = {}

                for change_path, details in changes.items():
                    if "parameters" in change_path:
                        param_changes[change_path] = details
                    elif "responses" in change_path:
                        response_changes[change_path] = details
                    else:
                        other_changes[change_path] = details

                # Parameter changes
                if param_changes:
                    sections.append("\nParameter Changes:")
                    for path, details in param_changes.items():
                        sections.append(f"- {path}")
                        sections.append(f"  - Old: ```{details['old']}```")
                        sections.append(f"  - New: ```{details['new']}```")

                # Response changes
                if response_changes:
                    sections.append("\nResponse Changes:")
                    for path, details in response_changes.items():
                        sections.append(f"- {path}")
                        sections.append(f"  - Old: ```{details['old']}```")
                        sections.append(f"  - New: ```{details['new']}```")

                # Other changes
                if other_changes:
                    sections.append("\nOther Changes:")
                    for path, details in other_changes.items():
                        sections.append(f"- {path}")
                        sections.append(f"  - Old: ```{details['old']}```")
                        sections.append(f"  - New: ```{details['new']}```")

                sections.append("")

        return "\n".join(sections)

    def _generate_consumer_impacts(self) -> str:

        if not self.consumer_impacts:
            return ""

        sections = ["## Consumer Impacts", ""]

        for impact in self.consumer_impacts:
            if not (
                impact.breaking_changes
                or impact.non_breaking_changes
                or impact.new_endpoints
                or impact.removed_endpoints
            ):
                continue

            symbol = "⚠️" if impact.has_breaking_changes else "ℹ️"
            sections.append(f"### {symbol} {impact.consumer.name}")
            sections.append(f"> {impact.consumer.description}")
            sections.append("")

            if impact.breaking_changes:
                sections.append("#### Breaking Changes")
                for change in impact.breaking_changes:
                    sections.append(f"- ⚠️ `{change.path}`")
                    for path, details in change.changes.items():
                        sections.append(f"  - {path}")
                        sections.append(f"    - Old: ```{details['old']}```")
                        sections.append(f"    - New: ```{details['new']}```")
                sections.append("")

            if impact.removed_endpoints:
                sections.append("#### Removed Endpoints")
                for path in impact.removed_endpoints:
                    sections.append(f"- 🗑️ `{path}`")
                sections.append("")

            if impact.non_breaking_changes:
                sections.append("#### Non-Breaking Changes")
                for change in impact.non_breaking_changes:
                    sections.append(f"- 📝 `{change.path}`")
                    for path, details in change.changes.items():
                        sections.append(f"  - {path}")
                        sections.append(f"    - Old: ```{details['old']}```")
                        sections.append(f"    - New: ```{details['new']}```")
                sections.append("")

            if impact.new_endpoints:
                sections.append("#### New Endpoints")
                for path in impact.new_endpoints:
                    sections.append(f"- ✨ `{path}`")
                sections.append("")

        return "\n".join(sections)
