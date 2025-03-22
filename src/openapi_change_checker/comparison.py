from typing import Dict, List, Tuple, NamedTuple
from openapi3 import OpenAPI
from openapi3.paths import Response

class Endpoint(NamedTuple):
    """Represents an API endpoint with its full details."""
    path: str
    method: str
    parameters: list
    responses: dict

class SpecComparison:
    """Compare OpenAPI specifications and identify changes."""

    def __init__(self, current_spec: Dict, previous_spec: Dict):
        """Initialize with two OpenAPI specifications to compare."""

        self.current_spec = OpenAPI(current_spec)
        self.previous_spec = OpenAPI(previous_spec)

        self.current_endpoints = self._get_endpoints(self.current_spec)
        self.previous_endpoints = self._get_endpoints(self.previous_spec)

    def _get_endpoints(self, spec: OpenAPI) -> List[Endpoint]:
        """Extract all endpoints with their details from a specification."""

        endpoints = []
        for path, path_item in spec.paths.items():

            # Common HTTP methods in OpenAPI
            methods = ['get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'trace']
            for method in methods:
                if hasattr(path_item, method) and getattr(path_item, method) is not None:
                    operation = getattr(path_item, method)
                    # Get parameters (combining path-level and operation-level parameters)
                    parameters = []
                    if hasattr(path_item, 'parameters'):
                        parameters.extend(path_item.parameters or [])
                    if hasattr(operation, 'parameters'):
                        parameters.extend(operation.parameters or [])
                    
                    # Get responses
                    responses = []
                    if hasattr(operation, 'responses'):
                        for r, r_item in operation.responses.items():
                            if isinstance(r_item, Response):
                                schema = r_item.content['application/json'].schema
                                re = r_item.raw_element
                                re['properties'] = schema.raw_element
                                responses.append({r: re})

                    endpoints.append(Endpoint(
                        path=path,
                        method=method.upper(),
                        parameters=parameters,
                        responses=responses
                    ))
        return endpoints

    def _get_endpoint_key(self, endpoint: Endpoint) -> Tuple[str, str]:
        """Get the key for comparing endpoints (path and method only)."""
        return (endpoint.path, endpoint.method)

    def _format_parameters(self, parameters: list) -> List[Dict]:
        formatted = []
        for param in parameters:
            formatted.append({
                'in': param.in_,
                'name': param.name,
                'schema': param.schema.type,
                'required': param.required if hasattr(param, 'required') else False,
                'nullable': param.allowEmptyValue if hasattr(param, 'allowEmptyValue') else False
            })
        return formatted

    def get_new_endpoints(self) -> List[str]:
        """Return list of new endpoints that only exist in current spec."""
        current_keys = {self._get_endpoint_key(e) for e in self.current_endpoints}
        previous_keys = {self._get_endpoint_key(e) for e in self.previous_endpoints}
        new_endpoint_keys = current_keys - previous_keys
        return sorted([f"{path} [{method}]" for path, method in new_endpoint_keys])

    def get_removed_endpoints(self) -> List[str]:
        """Return list of endpoints that only exist in previous spec."""
        current_keys = {self._get_endpoint_key(e) for e in self.current_endpoints}
        previous_keys = {self._get_endpoint_key(e) for e in self.previous_endpoints}
        removed_endpoint_keys = previous_keys - current_keys
        return sorted([f"{path} [{method}]" for path, method in removed_endpoint_keys])

    def get_modified_endpoints(self) -> List[Tuple[str, Dict]]:
        """Return list of modified endpoints and their changes."""
        modified = []
        
        # Create dictionaries mapping endpoint keys to their full details
        current_endpoints_dict = {self._get_endpoint_key(e): e for e in self.current_endpoints}
        previous_endpoints_dict = {self._get_endpoint_key(e): e for e in self.previous_endpoints}
        
        # Find endpoints that exist in both specs and convert to sorted list
        common_keys = sorted(list(set(current_endpoints_dict.keys()) & set(previous_endpoints_dict.keys())))
        
        for key in common_keys:
            current = current_endpoints_dict[key]
            previous = previous_endpoints_dict[key]
            changes = {}
            
            # Compare parameters
            current_params = self._format_parameters(current.parameters)
            previous_params = self._format_parameters(previous.parameters)
            if current_params != previous_params:
                changes['parameters'] = {
                    'previous': previous_params,
                    'current': current_params
                }
            
            # Compare responses
            if current.responses != previous.responses:
                changes['responses'] = {
                    'previous': previous.responses,
                    'current': current.responses
                }
            
            # If there are any changes, add to the modified list
            if changes:
                endpoint_str = f"{key[0]} [{key[1]}]"
                modified.append((endpoint_str, changes))
        
        return sorted(modified, key=lambda x: x[0])

    def is_breaking_change(self, path: str, changes: Dict) -> bool:
        """Determine if changes to an endpoint constitute a breaking change."""
        # This method might need to be updated to work with the new comparison logic
        # For now, keeping it as a placeholder that always returns False
        return False
