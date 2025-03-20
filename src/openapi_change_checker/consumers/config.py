import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class EndpointPattern:
    """Pattern for matching API endpoints."""

    path: str
    methods: List[str]

    def matches_endpoint(self, path: str, method: str) -> bool:

        # Check path match using fnmatch for wildcard support
        path_matches = fnmatch.fnmatch(path, self.path)

        # Check method match
        method_matches = "*" in self.methods or method.upper() in [
            m.upper() for m in self.methods
        ]

        return path_matches and method_matches


@dataclass
class ConsumerConfig:
    """Configuration for an API consumer."""

    name: str
    description: str
    endpoints: List[EndpointPattern]

    def is_affected_by_endpoint(self, path: str, method: str) -> bool:

        return any(pattern.matches_endpoint(path, method) for pattern in self.endpoints)


class ConsumerConfigLoader:
    """Load and parse consumer configurations."""

    @staticmethod
    def load_from_file(config_path: Path) -> List[ConsumerConfig]:

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path) as f:
                config_data = yaml.safe_load(f)

            if not isinstance(config_data, dict) or "consumers" not in config_data:
                raise ValueError("Invalid config file: missing 'consumers' section")

            consumers = []
            for name, data in config_data["consumers"].items():
                # Validate required fields
                if not isinstance(data, dict):
                    raise ValueError(f"Invalid consumer config for {name}")
                if "description" not in data or "endpoints" not in data:
                    raise ValueError(f"Missing required fields for consumer {name}")

                # Parse endpoint patterns
                endpoints = []
                for endpoint in data["endpoints"]:
                    if not isinstance(endpoint, dict):
                        raise ValueError(f"Invalid endpoint config for consumer {name}")
                    if "path" not in endpoint:
                        raise ValueError(
                            f"Missing path in endpoint config for consumer {name}"
                        )

                    methods = endpoint.get("methods", ["*"])
                    if not isinstance(methods, list):
                        raise ValueError(f"Invalid methods format for consumer {name}")

                    endpoints.append(
                        EndpointPattern(path=endpoint["path"], methods=methods)
                    )

                consumers.append(
                    ConsumerConfig(
                        name=name, description=data["description"], endpoints=endpoints
                    )
                )

            return consumers

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML format: {e}")
