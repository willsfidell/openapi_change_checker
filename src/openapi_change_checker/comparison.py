from typing import Dict, List, Set, Tuple

from deepdiff import DeepDiff


class SpecComparison:
    """Compare OpenAPI specifications and identify changes."""

    def __init__(self, current_spec: Dict, previous_spec: Dict):
        self.current_spec = current_spec
        self.previous_spec = previous_spec
        self._diff = DeepDiff(previous_spec, current_spec, ignore_order=True)

    def get_new_endpoints(self) -> List[str]:
        new_paths: Set[str] = set()

        # Check for new paths
        if "dictionary_item_added" in self._diff:
            for path in self._diff["dictionary_item_added"]:
                if path.startswith("root['paths']"):
                    # Extract the actual path from the DeepDiff path
                    endpoint = path.split("']['")[2].rstrip("']")
                    new_paths.add(endpoint)

        return sorted(new_paths)

    def get_removed_endpoints(self) -> List[str]:

        removed_paths: Set[str] = set()

        # Check for removed paths
        if "dictionary_item_removed" in self._diff:
            for path in self._diff["dictionary_item_removed"]:
                if path.startswith("root['paths']"):
                    # Extract the actual path from the DeepDiff path
                    endpoint = path.split("']['")[2].rstrip("']")
                    removed_paths.add(endpoint)

        return sorted(removed_paths)

    def get_modified_endpoints(self) -> List[Tuple[str, Dict]]:

        modified_paths: Dict[str, Dict] = {}

        # Check for value changes
        if "values_changed" in self._diff:
            for path, change in self._diff["values_changed"].items():
                if path.startswith("root['paths']"):
                    parts = path.split("']['")
                    endpoint = parts[2]
                    if endpoint not in modified_paths:
                        modified_paths[endpoint] = {}
                    # Add the change details
                    modified_paths[endpoint][".".join(parts[3:])] = {
                        "old": change["old_value"],
                        "new": change["new_value"],
                    }

        # Check for type changes
        if "type_changes" in self._diff:
            for path, change in self._diff["type_changes"].items():
                if path.startswith("root['paths']"):
                    parts = path.split("']['")
                    endpoint = parts[2]
                    if endpoint not in modified_paths:
                        modified_paths[endpoint] = {}
                    # Add the type change details
                    modified_paths[endpoint][".".join(parts[3:])] = {
                        "old_type": type(change["old_value"]).__name__,
                        "new_type": type(change["new_value"]).__name__,
                        "old": change["old_value"],
                        "new": change["new_value"],
                    }

        return [(k, v) for k, v in sorted(modified_paths.items())]

    def is_breaking_change(self, path: str, changes: Dict) -> bool:
        # Consider these changes as breaking:
        # 1. Required parameters added
        # 2. Parameters removed
        # 3. Response schema changes
        # 4. HTTP method removed
        # 5. Path parameter changes

        for change_path, details in changes.items():
            # Check for parameter changes
            if "parameters" in change_path:
                if isinstance(details.get("old"), list) and isinstance(
                    details.get("new"), list
                ):
                    old_required = {
                        p["name"] for p in details["old"] if p.get("required", False)
                    }
                    new_required = {
                        p["name"] for p in details["new"] if p.get("required", False)
                    }

                    # New required parameters
                    if len(new_required - old_required) > 0:
                        return True

                    # Removed parameters
                    old_params = {p["name"] for p in details["old"]}
                    new_params = {p["name"] for p in details["new"]}
                    if len(old_params - new_params) > 0:
                        return True

            # Check for response schema changes
            if "responses" in change_path and "schema" in change_path:
                return True

            # Check for removed HTTP methods
            if (
                len(change_path.split(".")) == 1
                and details.get("old")
                and not details.get("new")
            ):
                return True

        return False
