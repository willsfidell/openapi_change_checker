from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from ..comparison import SpecComparison
from .config import ConsumerConfig


@dataclass
class EndpointImpact:
    """Impact of changes to an endpoint."""

    path: str
    changes: Dict
    is_breaking: bool


@dataclass
class ConsumerImpact:
    """Impact analysis for a specific consumer."""

    consumer: ConsumerConfig
    breaking_changes: List[EndpointImpact]
    non_breaking_changes: List[EndpointImpact]
    new_endpoints: List[str]
    removed_endpoints: List[str]

    @property
    def has_breaking_changes(self) -> bool:
        """Check if there are any breaking changes."""
        return len(self.breaking_changes) > 0 or len(self.removed_endpoints) > 0


class ImpactAnalyzer:
    """Analyze the impact of API changes on consumers."""

    def __init__(self, comparison: SpecComparison, consumers: List[ConsumerConfig]):
        """Initialize the impact analyzer.

        Args:
            comparison (SpecComparison): The spec comparison results
            consumers (List[ConsumerConfig]): List of API consumers
        """
        self.comparison = comparison
        self.consumers = consumers

    def analyze_consumer_impacts(self) -> List[ConsumerImpact]:
        """Analyze impacts for all consumers.

        Returns:
            List[ConsumerImpact]: List of impact analyses for each consumer
        """
        impacts = []

        for consumer in self.consumers:
            # Get all changes affecting this consumer
            breaking_changes = []
            non_breaking_changes = []

            # Check modified endpoints
            for path, changes in self.comparison.get_modified_endpoints():
                # Get all methods affected by the changes
                methods = self._get_affected_methods(path, changes)

                # Check if any method is used by this consumer
                if any(
                    consumer.is_affected_by_endpoint(path, method) for method in methods
                ):
                    impact = EndpointImpact(
                        path=path,
                        changes=changes,
                        is_breaking=self.comparison.is_breaking_change(path, changes),
                    )
                    if impact.is_breaking:
                        breaking_changes.append(impact)
                    else:
                        non_breaking_changes.append(impact)

            # Check new endpoints
            new_endpoints = [
                path
                for path in self.comparison.get_new_endpoints()
                if consumer.is_affected_by_endpoint(path, "*")
            ]

            # Check removed endpoints
            removed_endpoints = [
                path
                for path in self.comparison.get_removed_endpoints()
                if consumer.is_affected_by_endpoint(path, "*")
            ]

            impacts.append(
                ConsumerImpact(
                    consumer=consumer,
                    breaking_changes=breaking_changes,
                    non_breaking_changes=non_breaking_changes,
                    new_endpoints=new_endpoints,
                    removed_endpoints=removed_endpoints,
                )
            )

        return impacts

    def _get_affected_methods(self, path: str, changes: Dict) -> Set[str]:
        """Get all HTTP methods affected by changes to an endpoint.

        Args:
            path (str): The endpoint path
            changes (Dict): The changes made to the endpoint

        Returns:
            Set[str]: Set of affected HTTP methods
        """
        methods = set()

        # Look for method-specific changes
        for change_path in changes.keys():
            # If the change path has only one part, it's a method change
            if "." not in change_path:
                methods.add(change_path.upper())
            # Otherwise, extract the method from the path if present
            else:
                method = change_path.split(".")[0].upper()
                if method in {
                    "GET",
                    "POST",
                    "PUT",
                    "DELETE",
                    "PATCH",
                    "HEAD",
                    "OPTIONS",
                }:
                    methods.add(method)

        # If no specific methods found, assume all methods are affected
        if not methods:
            methods.add("*")

        return methods
