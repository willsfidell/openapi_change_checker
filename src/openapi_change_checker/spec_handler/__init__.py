from abc import ABC, abstractmethod
from typing import Dict, Optional


class SpecHandler(ABC):
    """Base class for OpenAPI specification handlers."""

    @abstractmethod
    def get_current_spec(self) -> Dict:
        """Get the current OpenAPI specification.

        Returns:
            Dict: The current OpenAPI specification as a dictionary
        """
        pass

    @abstractmethod
    def get_previous_spec(self, pr_number: int) -> Optional[Dict]:
        """Get the previous OpenAPI specification from the target branch.

        Args:
            pr_number (int): Pull request number to get target branch from

        Returns:
            Optional[Dict]: The previous OpenAPI specification as a dictionary,
                          or None if no previous spec exists
        """
        pass

    def validate_spec(self, spec: Dict) -> bool:
        """Validate that the given dictionary is a valid OpenAPI specification.

        Args:
            spec (Dict): The specification to validate

        Returns:
            bool: True if valid, False otherwise
        """
        # TODO: Implement OpenAPI schema validation
        required_fields = ["openapi", "info", "paths"]
        return all(field in spec for field in required_fields)
