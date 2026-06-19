"""
Azure Cognitive Search Client Module

This module provides a client for retrieving product guidance and enrichment data
from Azure Cognitive Search. It's designed for Product Information Management (PIM)
systems to perform semantic searches and retrieve relevant documentation.

Classes:
    AzureSearchClient: Wrapper around Azure Cognitive Search API for semantic retrieval

Example:
    >>> from src.clients.azure_search_client import AzureSearchClient
    >>> client = AzureSearchClient()
    >>> results = client.retrieve_guidance("laptop specifications")
    >>> print(results)
    [{'id': '1', 'title': 'Laptop Specs', 'content': '...', 'tags': ['tech']}, ...]

Raises:
    ValueError: If configuration is invalid or query is empty
    azure.core.exceptions.AzureError: If Azure Search API call fails
"""

import logging
from typing import Optional, List, Dict, Any
from azure.core.credentials import AzureKeyCredential  # type: ignore
from azure.core.exceptions import AzureError, HttpResponseError  # type: ignore
from azure.search.documents import SearchClient  # type: ignore
from src.config import settings

logger = logging.getLogger(__name__)


class AzureSearchClient:
    """
    Client for retrieving search results from Azure Cognitive Search.

    This client handles communication with Azure Cognitive Search to retrieve
    product guidance, enrichment data, and documentation. It provides error
    handling, logging, input validation, and response validation.

    Attributes:
        client (SearchClient): Azure Search client instance
        index_name (str): Search index name from settings
        default_top_k (int): Default number of results to return

    Raises:
        ValueError: If required configuration is missing

    Example:
        >>> client = AzureSearchClient()
        >>> results = client.retrieve_guidance(
        ...     "product specifications",
        ...     top_k=5
        ... )
        >>> for result in results:
        ...     print(result["title"])
    """

    # Configuration constraints
    MIN_TOP_K = 1
    MAX_TOP_K = 100
    MAX_QUERY_LENGTH = 1000

    def __init__(self):
        """
        Initialize Azure Search client with configuration from settings.

        Validates that all required configuration values are present and creates
        the SearchClient instance for use in other methods.

        Raises:
            ValueError: If any required configuration is missing
            AzureError: If client initialization fails

        Example:
            >>> client = AzureSearchClient()
        """
        # Validate configuration
        self._validate_config()

        try:
            self.client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=settings.azure_search_index,
                credential=AzureKeyCredential(settings.azure_search_api_key),
            )
            self.index_name = settings.azure_search_index
            self.default_top_k = settings.default_top_k or 10
            logger.info(f"Azure Search client initialized for index: {self.index_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Search client: {str(e)}")
            raise

    def _validate_config(self) -> None:
        """
        Validate that all required configuration values are present.

        Checks for:
        - azure_search_endpoint
        - azure_search_index
        - azure_search_api_key
        - default_top_k (optional, uses default if missing)

        Raises:
            ValueError: If any required configuration is missing or invalid

        Example:
            >>> client._validate_config()  # Called automatically in __init__
        """
        required_configs = {
            "azure_search_endpoint": settings.azure_search_endpoint,
            "azure_search_index": settings.azure_search_index,
            "azure_search_api_key": settings.azure_search_api_key,
        }

        missing = [key for key, value in required_configs.items() if not value]

        if missing:
            error_msg = f"Missing required configuration: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug("Configuration validation passed")

    def retrieve_guidance(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve search results from Azure Cognitive Search.

        Searches the configured index using the provided query and returns a list
        of matching documents. Results are limited to the specified number (top_k).
        Uses semantic search if available in the index.

        Args:
            query (str): Search query string. Supports keyword and semantic search.
                        Max length: 1000 characters.
            top_k (Optional[int]): Maximum number of results to return.
                                  If None, uses default_top_k (usually 10).
                                  Valid range: 1-100.

        Returns:
            List[Dict[str, Any]]: List of search result documents containing:
                - id (str): Document identifier
                - title (str): Document title
                - content (str): Document content
                - tags (List[str]): Associated tags/keywords

        Raises:
            ValueError: If query is invalid or top_k is out of range
            HttpResponseError: If Azure Search API returns an error
            AzureError: If connection to Azure Search fails

        Example:
            >>> client = AzureSearchClient()
            >>> results = client.retrieve_guidance("laptop specifications", top_k=5)
            >>> if results:
            ...     print(f"Found {len(results)} results")
            ...     for result in results:
            ...         print(f"- {result['title']}")
            ... else:
            ...     print("No results found")
        """
        # Validate inputs
        self._validate_query(query)
        self._validate_top_k(top_k)

        # Use default if not specified
        effective_top_k = top_k or self.default_top_k

        logger.info(f"Retrieving guidance for query: '{query}' (top_k: {effective_top_k})")

        try:
            # Execute search
            results = self.client.search(
                search_text=query,
                top=effective_top_k
            )

            # Extract and validate results
            documents = self._extract_results(results)

            if not documents:
                logger.warning(f"No results found for query: '{query}'")
            else:
                logger.info(f"Retrieved {len(documents)} results for query: '{query}'")

            return documents

        except HttpResponseError as e:
            logger.error(f"Azure Search API error for query '{query}': {str(e)}")
            raise
        except AzureError as e:
            logger.error(f"Azure connection error for query '{query}': {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving guidance for '{query}': {str(e)}")
            raise

    def _validate_query(self, query: str) -> None:
        """
        Validate search query before sending to Azure Search.

        Checks for:
        - Query is not None
        - Query is not empty or whitespace
        - Query does not exceed max length

        Args:
            query (str): Query to validate

        Raises:
            ValueError: If query is invalid

        Example:
            >>> client._validate_query("laptop specifications")  # OK
            >>> client._validate_query("")  # Raises ValueError
        """
        if query is None:
            logger.warning("Query is None")
            raise ValueError("Query cannot be None")

        if not isinstance(query, str):
            logger.warning(f"Query is not a string: {type(query)}")
            raise ValueError(f"Query must be a string, not {type(query).__name__}")

        if not query.strip():
            logger.warning("Query is empty or whitespace only")
            raise ValueError("Query cannot be empty")

        if len(query) > self.MAX_QUERY_LENGTH:
            logger.warning(f"Query exceeds max length: {len(query)} > {self.MAX_QUERY_LENGTH}")
            raise ValueError(f"Query exceeds maximum length of {self.MAX_QUERY_LENGTH} characters")

        logger.debug(f"Query validation passed (length: {len(query)})")

    def _validate_top_k(self, top_k: Optional[int]) -> None:
        """
        Validate top_k parameter.

        Checks for:
        - top_k is None or an integer
        - If provided, top_k is in valid range (1-100)

        Args:
            top_k (Optional[int]): Number of results to validate

        Raises:
            ValueError: If top_k is invalid

        Example:
            >>> client._validate_top_k(5)  # OK
            >>> client._validate_top_k(None)  # OK
            >>> client._validate_top_k(0)  # Raises ValueError
        """
        if top_k is None:
            return  # None is OK, will use default

        if not isinstance(top_k, int):
            logger.warning(f"top_k is not an integer: {type(top_k)}")
            raise ValueError(f"top_k must be an integer, not {type(top_k).__name__}")

        if top_k < self.MIN_TOP_K or top_k > self.MAX_TOP_K:
            logger.warning(f"top_k out of range: {top_k} (valid: {self.MIN_TOP_K}-{self.MAX_TOP_K})")
            raise ValueError(f"top_k must be between {self.MIN_TOP_K} and {self.MAX_TOP_K}, got {top_k}")

        logger.debug(f"top_k validation passed: {top_k}")

    def _extract_results(self, results: Any) -> List[Dict[str, Any]]:
        """
        Extract and validate search results from Azure Search response.

        Converts raw search results into a structured list of dictionaries,
        extracting only the fields we need. Validates that required fields
        are present in each result.

        Args:
            results: Raw results from Azure Search API

        Returns:
            List[Dict[str, Any]]: Extracted and validated search results

        Raises:
            ValueError: If result structure is invalid

        Example:
            >>> results = client.client.search(search_text="query")
            >>> extracted = client._extract_results(results)
        """
        documents = []

        try:
            for item in results:
                # Extract required fields
                doc_id = item.get("id")
                title = item.get("title")
                content = item.get("content")
                tags = item.get("tags")

                # Validate required fields
                if not doc_id:
                    logger.warning("Search result missing 'id' field, skipping")
                    continue

                if not title:
                    logger.warning(f"Search result {doc_id} missing 'title' field, skipping")
                    continue

                if not content:
                    logger.warning(f"Search result {doc_id} missing 'content' field, skipping")
                    continue

                # Build result document
                document = {
                    "id": doc_id,
                    "title": title,
                    "content": content,
                    "tags": tags or []  # Default to empty list if no tags
                }

                documents.append(document)

            return documents

        except Exception as e:
            logger.error(f"Error extracting search results: {str(e)}")
            raise ValueError(f"Failed to extract search results: {str(e)}")
