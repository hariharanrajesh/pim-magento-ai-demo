"""
Magento Client Module

This module provides a client for updating product information in Magento via REST API.
It handles authentication, product content updates, and error handling for PIM integration.

Classes:
    MagentoClient: Wrapper around Magento REST API for product updates

Example:
    >>> from src.clients.magento_client import MagentoClient
    >>> client = MagentoClient()
    >>> result = client.update_product_content(
    ...     sku="SKU-123",
    ...     title="Product Title",
    ...     long_description="Product description..."
    ... )
    >>> print(result)
    {'id': 1, 'sku': 'SKU-123', 'name': 'Product Title', ...}

Raises:
    ValueError: If configuration is invalid or input is invalid
    requests.RequestException: If API call fails
"""

import logging
import time
from typing import Optional, Dict, Any
import requests
from requests.exceptions import RequestException, ConnectionError, Timeout, HTTPError
from src.config import settings

logger = logging.getLogger(__name__)


class MagentoClient:
    """
    Client for updating product information in Magento.

    This client handles authentication, product content updates, and error handling
    for integration with Magento REST API. It includes token caching, input validation,
    and comprehensive error handling.

    Attributes:
        base_url (str): Magento instance base URL
        username (str): Admin username for authentication
        password (str): Admin password for authentication
        store_code (str): Magento store code
        _token (Optional[str]): Cached admin token
        _token_expires_at (float): Token expiration timestamp

    Raises:
        ValueError: If required configuration is missing

    Example:
        >>> client = MagentoClient()
        >>> result = client.update_product_content(
        ...     sku="SKU-001",
        ...     title="Laptop Pro",
        ...     long_description="High-performance laptop..."
        ... )
        >>> print(result["sku"])
        'SKU-001'
    """

    # Configuration constants
    TOKEN_ENDPOINT = "/rest/V1/integration/admin/token"
    PRODUCT_ENDPOINT = "/rest/V1/products/{sku}"
    DEFAULT_TIMEOUT = 30
    TOKEN_CACHE_TTL = 3600  # 1 hour

    # Constraints
    MIN_SKU_LENGTH = 1
    MAX_SKU_LENGTH = 64
    MIN_TITLE_LENGTH = 1
    MAX_TITLE_LENGTH = 255
    MIN_DESCRIPTION_LENGTH = 0
    MAX_DESCRIPTION_LENGTH = 10000

    def __init__(self):
        """
        Initialize Magento client with configuration from settings.

        Validates that all required configuration values are present before
        creating the client instance.

        Raises:
            ValueError: If any required configuration is missing

        Example:
            >>> client = MagentoClient()
        """
        # Validate configuration
        self._validate_config()

        # Initialize attributes
        self.base_url = settings.magento_base_url.rstrip("/")
        self.username = settings.magento_admin_username
        self.password = settings.magento_admin_password
        self.store_code = settings.magento_store_code

        # Token caching
        self._token: Optional[str] = None
        self._token_expires_at: float = 0

        logger.info(f"Magento client initialized for: {self.base_url}")

    def _validate_config(self) -> None:
        """
        Validate that all required configuration values are present.

        Checks for:
        - magento_base_url
        - magento_admin_username
        - magento_admin_password
        - magento_store_code

        Raises:
            ValueError: If any required configuration is missing

        Example:
            >>> client._validate_config()  # Called automatically in __init__
        """
        required_configs = {
            "magento_base_url": settings.magento_base_url,
            "magento_admin_username": settings.magento_admin_username,
            "magento_admin_password": settings.magento_admin_password,
            "magento_store_code": settings.magento_store_code,
        }

        missing = [key for key, value in required_configs.items() if not value]

        if missing:
            error_msg = f"Missing required Magento configuration: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug("Magento configuration validation passed")

    def get_admin_token(self) -> str:
        """
        Get or retrieve admin authentication token from Magento.

        Implements token caching to avoid repeated authentication calls.
        If cached token is valid (not expired), returns cached token.
        Otherwise, authenticates with Magento and caches new token.

        Returns:
            str: Admin authentication token for use in API requests

        Raises:
            ConnectionError: If unable to connect to Magento
            Timeout: If request times out
            HTTPError: If Magento returns HTTP error
            ValueError: If response is not valid JSON or missing token

        Example:
            >>> token = client.get_admin_token()
            >>> print(f"Token: {token[:20]}...")
            'Token: eyJhbGciOiJIUzI1NiIs...'
        """
        # Return cached token if still valid
        if self._token and self._is_token_valid():
            logger.debug("Using cached admin token")
            return self._token

        logger.info("Fetching new admin token from Magento")

        try:
            url = f"{self.base_url}{self.TOKEN_ENDPOINT}"

            payload = {
                "username": self.username,
                "password": self.password
            }

            response = requests.post(
                url,
                json=payload,
                timeout=self.DEFAULT_TIMEOUT
            )
            response.raise_for_status()

            # Extract and validate token
            token = response.json()
            if not isinstance(token, str):
                logger.error(f"Invalid token response type: {type(token)}")
                raise ValueError(f"Expected string token, got {type(token).__name__}")

            # Cache token
            self._token = token
            self._token_expires_at = time.time() + self.TOKEN_CACHE_TTL

            logger.info("Successfully retrieved admin token")
            return token

        except ConnectionError as e:
            logger.error(f"Connection error fetching token: {str(e)}")
            raise
        except Timeout as e:
            logger.error(f"Timeout fetching token: {str(e)}")
            raise
        except HTTPError as e:
            logger.error(f"HTTP error fetching token: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Token validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching token: {str(e)}")
            raise

    def _is_token_valid(self) -> bool:
        """
        Check if cached token is still valid (not expired).

        Returns:
            bool: True if token is still valid, False if expired

        Example:
            >>> is_valid = client._is_token_valid()
        """
        is_valid = time.time() < self._token_expires_at
        logger.debug(f"Token valid: {is_valid}")
        return is_valid

    def update_product_content(
        self,
        sku: str,
        title: str,
        long_description: str
    ) -> Dict[str, Any]:
        """
        Update product content in Magento.

        Updates the product name and description for the specified SKU.
        Authenticates with Magento using cached token and sends update
        via REST API.

        Args:
            sku (str): Product SKU (1-64 characters)
            title (str): Product title/name (1-255 characters)
            long_description (str): Product description (max 10,000 characters)

        Returns:
            Dict[str, Any]: API response containing updated product data

        Raises:
            ValueError: If inputs are invalid
            ConnectionError: If unable to connect to Magento
            Timeout: If request times out
            HTTPError: If Magento returns HTTP error

        Example:
            >>> result = client.update_product_content(
            ...     sku="SKU-001",
            ...     title="Laptop Pro",
            ...     long_description="High-performance laptop with..."
            ... )
            >>> print(result["id"])
            123
        """
        # Validate inputs
        self._validate_sku(sku)
        self._validate_title(title)
        self._validate_description(long_description)

        logger.info(f"Updating product content for SKU: {sku}")

        try:
            # Get authentication token
            token = self.get_admin_token()

            # Build API URL
            url = f"{self.base_url}{self.PRODUCT_ENDPOINT.format(sku=sku)}"

            # Build payload
            payload = {
                "product": {
                    "sku": sku,
                    "name": title,
                    "custom_attributes": [
                        {
                            "attribute_code": "description",
                            "value": long_description
                        }
                    ]
                }
            }

            # Build headers
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            # Send request
            response = requests.put(
                url,
                json=payload,
                headers=headers,
                timeout=self.DEFAULT_TIMEOUT
            )
            response.raise_for_status()

            # Extract and validate response
            result = response.json()
            if not isinstance(result, dict):
                logger.error(f"Invalid response type: {type(result)}")
                raise ValueError(f"Expected dict response, got {type(result).__name__}")

            logger.info(f"Successfully updated product content for SKU: {sku}")
            return result

        except ConnectionError as e:
            logger.error(f"Connection error updating product {sku}: {str(e)}")
            raise
        except Timeout as e:
            logger.error(f"Timeout updating product {sku}: {str(e)}")
            raise
        except HTTPError as e:
            logger.error(f"HTTP error updating product {sku}: {str(e)}")
            raise
        except ValueError as e:
            logger.error(f"Validation error updating product {sku}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating product {sku}: {str(e)}")
            raise

    def _validate_sku(self, sku: str) -> None:
        """
        Validate SKU parameter.

        Checks for:
        - SKU is not None
        - SKU is a string
        - SKU is not empty
        - SKU length within valid range

        Args:
            sku (str): SKU to validate

        Raises:
            ValueError: If SKU is invalid

        Example:
            >>> client._validate_sku("SKU-001")  # OK
            >>> client._validate_sku("")  # Raises ValueError
        """
        if sku is None:
            logger.warning("SKU is None")
            raise ValueError("SKU cannot be None")

        if not isinstance(sku, str):
            logger.warning(f"SKU is not a string: {type(sku)}")
            raise ValueError(f"SKU must be a string, not {type(sku).__name__}")

        if not sku.strip():
            logger.warning("SKU is empty or whitespace only")
            raise ValueError("SKU cannot be empty")

        sku = sku.strip()

        if len(sku) < self.MIN_SKU_LENGTH or len(sku) > self.MAX_SKU_LENGTH:
            logger.warning(f"SKU length out of range: {len(sku)} (valid: {self.MIN_SKU_LENGTH}-{self.MAX_SKU_LENGTH})")
            raise ValueError(f"SKU must be {self.MIN_SKU_LENGTH}-{self.MAX_SKU_LENGTH} characters, got {len(sku)}")

        logger.debug(f"SKU validation passed: {sku}")

    def _validate_title(self, title: str) -> None:
        """
        Validate product title parameter.

        Checks for:
        - Title is not None
        - Title is a string
        - Title is not empty
        - Title length within valid range

        Args:
            title (str): Title to validate

        Raises:
            ValueError: If title is invalid

        Example:
            >>> client._validate_title("Laptop Pro")  # OK
            >>> client._validate_title("")  # Raises ValueError
        """
        if title is None:
            logger.warning("Title is None")
            raise ValueError("Title cannot be None")

        if not isinstance(title, str):
            logger.warning(f"Title is not a string: {type(title)}")
            raise ValueError(f"Title must be a string, not {type(title).__name__}")

        if not title.strip():
            logger.warning("Title is empty or whitespace only")
            raise ValueError("Title cannot be empty")

        title = title.strip()

        if len(title) < self.MIN_TITLE_LENGTH or len(title) > self.MAX_TITLE_LENGTH:
            logger.warning(f"Title length out of range: {len(title)} (valid: {self.MIN_TITLE_LENGTH}-{self.MAX_TITLE_LENGTH})")
            raise ValueError(f"Title must be {self.MIN_TITLE_LENGTH}-{self.MAX_TITLE_LENGTH} characters, got {len(title)}")

        logger.debug("Title validation passed")

    def _validate_description(self, description: str) -> None:
        """
        Validate product description parameter.

        Checks for:
        - Description is not None
        - Description is a string
        - Description length within valid range (empty allowed)

        Args:
            description (str): Description to validate

        Raises:
            ValueError: If description is invalid

        Example:
            >>> client._validate_description("Product description here")  # OK
            >>> client._validate_description("")  # OK (empty allowed)
        """
        if description is None:
            logger.warning("Description is None")
            raise ValueError("Description cannot be None")

        if not isinstance(description, str):
            logger.warning(f"Description is not a string: {type(description)}")
            raise ValueError(f"Description must be a string, not {type(description).__name__}")

        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            logger.warning(f"Description too long: {len(description)} > {self.MAX_DESCRIPTION_LENGTH}")
            raise ValueError(f"Description exceeds maximum length of {self.MAX_DESCRIPTION_LENGTH} characters")

        logger.debug(f"Description validation passed (length: {len(description)})")
