"""Home Assistant API client wrapper."""

from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urljoin
import os
import requests
from dotenv import load_dotenv


class HAClient:
    """Direct Home Assistant REST API client."""

    def __init__(self, url: Optional[str] = None, token: Optional[str] = None):
        """
        Initialize Home Assistant client.

        Args:
            url: Home Assistant URL (e.g., http://192.168.1.100:8123)
                 If not provided, loads from HA_URL environment variable
            token: Long-lived access token
                   If not provided, loads from HA_TOKEN environment variable
        """
        # Load environment variables from .env file
        load_dotenv()

        # Use provided values or fall back to environment variables
        self.url = url or os.getenv('HA_URL')
        self.token = token or os.getenv('HA_TOKEN')

        if not self.url:
            raise ValueError(
                "Home Assistant URL not provided. "
                "Set HA_URL environment variable or pass url parameter."
            )
        if not self.token:
            raise ValueError(
                "Home Assistant token not provided. "
                "Set HA_TOKEN environment variable or pass token parameter."
            )

        # Parse URL to extract host and port
        # If URL doesn't have a scheme, add http://
        if not self.url.startswith(('http://', 'https://')):
            self.url = f'http://{self.url}'

        # Ensure URL ends without trailing slash
        self.url = self.url.rstrip('/')

        parsed = urlparse(self.url)
        self.host = parsed.hostname or 'localhost'
        self.port = parsed.port or 8123
        self.use_ssl = parsed.scheme == 'https'

        # Setup request headers
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }

        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make a request to the Home Assistant API.

        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint (e.g., '/api/states')
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            requests.RequestException: On request failure
        """
        url = urljoin(self.url, endpoint)
        response = self.session.request(method, url, timeout=10, **kwargs)
        response.raise_for_status()
        return response

    def test_connection(self) -> bool:
        """
        Test the connection to Home Assistant.

        Returns:
            True if connection is successful

        Raises:
            Exception if connection fails
        """
        try:
            response = self._request('GET', '/api/')
            data = response.json()
            return data.get('message') == 'API running.'
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Home Assistant: {e}")

    def get_config(self) -> Dict[str, Any]:
        """
        Get Home Assistant configuration.

        Returns:
            Configuration dictionary
        """
        response = self._request('GET', '/api/config')
        return response.json()

    def get_states(self, entity_id: Optional[str] = None) -> Any:
        """
        Get state(s) from Home Assistant.

        Args:
            entity_id: Optional entity ID. If None, returns all states.

        Returns:
            State dictionary or list of states
        """
        if entity_id:
            response = self._request('GET', f'/api/states/{entity_id}')
        else:
            response = self._request('GET', '/api/states')
        return response.json()

    def call_service(self, domain: str, service: str, service_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Call a Home Assistant service.

        Args:
            domain: Service domain (e.g., 'automation')
            service: Service name (e.g., 'turn_on')
            service_data: Optional service data

        Returns:
            Service response
        """
        endpoint = f'/api/services/{domain}/{service}'
        response = self._request('POST', endpoint, json=service_data or {})
        return response.json() if response.text else {}

    def get_entities(self) -> Dict[str, Any]:
        """
        Get all entities (states).

        Returns:
            Dictionary with entities
        """
        states = self.get_states()
        return {'entities': states}

    def create_automation(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new automation in Home Assistant.

        Args:
            config: Automation configuration dictionary with:
                - id: unique ID
                - alias: name
                - trigger: list of triggers
                - action: list of actions
                - condition: optional conditions
                - mode: optional mode (default: single)

        Returns:
            Response from Home Assistant

        Raises:
            requests.RequestException: On request failure
        """
        endpoint = '/api/config/automation/config'
        response = self._request('POST', endpoint, json=config)
        return response.json() if response.text else {}

    def update_automation(self, automation_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update existing automation.

        Args:
            automation_id: The automation ID (not entity_id)
            config: Updated automation configuration

        Returns:
            Response from Home Assistant

        Raises:
            requests.RequestException: On request failure
        """
        endpoint = f'/api/config/automation/config/{automation_id}'
        response = self._request('PUT', endpoint, json=config)
        return response.json() if response.text else {}

    def __repr__(self) -> str:
        """String representation of the client."""
        return f"HAClient(host={self.host}, port={self.port}, ssl={self.use_ssl})"
