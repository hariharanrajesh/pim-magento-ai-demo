"""
Azure OpenAI Client Module

This module provides a client for generating structured JSON content using Azure OpenAI's
Chat Completion API. It's designed for Product Information Management (PIM) systems to
generate product descriptions, metadata, and enriched content.

Classes:
    AzureOpenAIClient: Wrapper around Azure OpenAI API for structured content generation

Example:
    >>> from src.clients.azure_openai_client import AzureOpenAIClient
    >>> client = AzureOpenAIClient()
    >>> prompt = "Generate product metadata for a laptop"
    >>> content = client.generate_structured_content(prompt)
    >>> print(content)
    {'title': 'High-Performance Laptop', 'description': '...', ...}

Raises:
    ValueError: If configuration is invalid or prompt is empty
    json.JSONDecodeError: If API response is not valid JSON
    openai.APIError: If Azure OpenAI API call fails
"""

import json
import logging
from typing import Optional
from openai import AzureOpenAI, APIError, APIConnectionError  # type: ignore
from src.config import settings

logger = logging.getLogger(__name__)


class AzureOpenAIClient:
    """
    Client for generating structured JSON content using Azure OpenAI.

    This client handles communication with Azure OpenAI's API to generate
    structured product content in JSON format. It provides error handling,
    logging, and validation for production use.

    Attributes:
        client (AzureOpenAI): Azure OpenAI client instance
        deployment_name (str): Chat deployment name from settings

    Raises:
        ValueError: If required configuration is missing

    Example:
        >>> client = AzureOpenAIClient()
        >>> result = client.generate_structured_content(
        ...     "Generate content for a smartphone"
        ... )
        >>> print(result["title"])
        'Latest Smartphone Model'
    """

    # Default system prompt for JSON generation
    SYSTEM_PROMPT = "You are a product content expert. Generate accurate, structured JSON for product information."

    # Constraints
    MAX_PROMPT_LENGTH = 4000
    TEMPERATURE = 0.4  # Low temperature for consistency

    def __init__(self):
        """
        Initialize Azure OpenAI client with configuration from settings.

        Validates that all required configuration values are present before
        creating the client instance.

        Raises:
            ValueError: If any required configuration is missing

        Example:
            >>> client = AzureOpenAIClient()
        """
        # Validate configuration
        self._validate_config()

        # Initialize Azure OpenAI client
        try:
            self.client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
            )
            self.deployment_name = settings.azure_openai_chat_deployment
            logger.info("Azure OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
            raise

    def _validate_config(self) -> None:
        """
        Validate that all required configuration values are present.

        Checks for:
        - azure_openai_endpoint
        - azure_openai_api_key
        - azure_openai_api_version
        - azure_openai_chat_deployment

        Raises:
            ValueError: If any required configuration is missing or invalid

        Example:
            >>> client._validate_config()  # Called automatically in __init__
        """
        required_configs = {
            "azure_openai_endpoint": settings.azure_openai_endpoint,
            "azure_openai_api_key": settings.azure_openai_api_key,
            "azure_openai_api_version": settings.azure_openai_api_version,
            "azure_openai_chat_deployment": settings.azure_openai_chat_deployment,
        }

        missing = [key for key, value in required_configs.items() if not value]

        if missing:
            error_msg = f"Missing required configuration: {', '.join(missing)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug("Configuration validation passed")

    def generate_structured_content(self, prompt: str) -> dict:
        """
        Generate structured JSON content from a user prompt using Azure OpenAI.

        Sends a prompt to Azure OpenAI's Chat Completion API with JSON response
        mode enabled, ensuring the response is always valid JSON. Uses a low
        temperature (0.4) for consistent, deterministic outputs.

        Args:
            prompt (str): User prompt describing the content to generate.
                         Should clearly specify desired JSON structure.
                         Max length: 4000 characters.

        Returns:
            dict: Parsed JSON response from Azure OpenAI containing generated content.
                  Structure depends on the prompt but should follow the schema
                  requested in the prompt.

        Raises:
            ValueError: If prompt is empty, None, or exceeds max length
            json.JSONDecodeError: If API response is not valid JSON
            APIConnectionError: If connection to Azure OpenAI fails
            APIError: If Azure OpenAI API returns an error

        Example:
            >>> client = AzureOpenAIClient()
            >>> prompt = '''Generate product metadata with this JSON structure:
            ... {
            ...   "title": "string",
            ...   "description": "string",
            ...   "features": ["string"]
            ... }
            ... For: A wireless headphone'''
            >>> content = client.generate_structured_content(prompt)
            >>> print(content["title"])
            'Premium Wireless Headphones'
        """
        # Validate input
        self._validate_prompt(prompt)

        logger.info(f"Generating structured content (prompt length: {len(prompt)} chars)")

        try:
            # Call Azure OpenAI API
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.TEMPERATURE,
            )

            # Extract and validate response
            if not response.choices or not response.choices[0].message.content:
                logger.error("Empty response from Azure OpenAI API")
                raise ValueError("Empty response from API")

            # Parse JSON response
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                logger.info("Successfully generated structured content")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.debug(f"Raw response: {content}")
                raise ValueError(f"API response is not valid JSON: {str(e)}")

        except APIConnectionError as e:
            logger.error(f"Connection error to Azure OpenAI: {str(e)}")
            raise
        except APIError as e:
            logger.error(f"Azure OpenAI API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating content: {str(e)}")
            raise

    def _validate_prompt(self, prompt: str) -> None:
        """
        Validate user prompt before sending to Azure OpenAI.

        Checks for:
        - Prompt is not None
        - Prompt is not empty
        - Prompt does not exceed max length

        Args:
            prompt (str): Prompt to validate

        Raises:
            ValueError: If prompt is invalid

        Example:
            >>> client._validate_prompt("Generate product content")  # OK
            >>> client._validate_prompt("")  # Raises ValueError
        """
        if prompt is None:
            logger.warning("Prompt is None")
            raise ValueError("Prompt cannot be None")

        if not isinstance(prompt, str):
            logger.warning(f"Prompt is not a string: {type(prompt)}")
            raise ValueError(f"Prompt must be a string, not {type(prompt).__name__}")

        if not prompt.strip():
            logger.warning("Prompt is empty or whitespace only")
            raise ValueError("Prompt cannot be empty")

        if len(prompt) > self.MAX_PROMPT_LENGTH:
            logger.warning(f"Prompt exceeds max length: {len(prompt)} > {self.MAX_PROMPT_LENGTH}")
            raise ValueError(f"Prompt exceeds maximum length of {self.MAX_PROMPT_LENGTH} characters")

        logger.debug(f"Prompt validation passed (length: {len(prompt)})")
