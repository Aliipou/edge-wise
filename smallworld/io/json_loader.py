"""
JSON Loader Module

Handles loading service topology data from JSON files and strings.
Validates input against defined schemas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from smallworld.io.schemas import AnalyzeRequest, ServiceTopology


class JsonLoaderError(Exception):
    """Base exception for JSON loading errors."""

    pass


class JsonLoader:
    """
    Loads and validates service topology from JSON sources.
    """

    @staticmethod
    def load_from_file(file_path: str | Path) -> ServiceTopology:
        """
        Load service topology from a JSON file.

        Args:
            file_path: Path to the JSON file.

        Returns:
            Validated ServiceTopology object.

        Raises:
            JsonLoaderError: If file cannot be read or parsed.
        """
        path = Path(file_path)

        if not path.exists():
            raise JsonLoaderError(f"File not found: {file_path}")

        if not path.is_file():
            raise JsonLoaderError(f"Not a file: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise JsonLoaderError(f"Invalid JSON: {e}")
        except IOError as e:
            raise JsonLoaderError(f"Cannot read file: {e}")

        return JsonLoader.load_from_dict(data)

    @staticmethod
    def load_from_string(json_string: str) -> ServiceTopology:
        """
        Load service topology from a JSON string.

        Args:
            json_string: JSON string containing topology data.

        Returns:
            Validated ServiceTopology object.

        Raises:
            JsonLoaderError: If string cannot be parsed.
        """
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise JsonLoaderError(f"Invalid JSON: {e}")

        return JsonLoader.load_from_dict(data)

    @staticmethod
    def load_from_dict(data: dict[str, Any]) -> ServiceTopology:
        """
        Load service topology from a dictionary.

        Args:
            data: Dictionary containing topology data.

        Returns:
            Validated ServiceTopology object.

        Raises:
            JsonLoaderError: If data validation fails.
        """
        try:
            return ServiceTopology.model_validate(data)
        except Exception as e:
            raise JsonLoaderError(f"Validation error: {e}")

    @staticmethod
    def load_request_from_file(file_path: str | Path) -> AnalyzeRequest:
        """
        Load a full analyze request from a JSON file.

        Args:
            file_path: Path to the JSON file.

        Returns:
            Validated AnalyzeRequest object.

        Raises:
            JsonLoaderError: If file cannot be read or parsed.
        """
        path = Path(file_path)

        if not path.exists():
            raise JsonLoaderError(f"File not found: {file_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise JsonLoaderError(f"Invalid JSON: {e}")
        except IOError as e:
            raise JsonLoaderError(f"Cannot read file: {e}")

        return JsonLoader.load_request_from_dict(data)

    @staticmethod
    def load_request_from_string(json_string: str) -> AnalyzeRequest:
        """
        Load a full analyze request from a JSON string.

        Args:
            json_string: JSON string containing request data.

        Returns:
            Validated AnalyzeRequest object.

        Raises:
            JsonLoaderError: If string cannot be parsed.
        """
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise JsonLoaderError(f"Invalid JSON: {e}")

        return JsonLoader.load_request_from_dict(data)

    @staticmethod
    def load_request_from_dict(data: dict[str, Any]) -> AnalyzeRequest:
        """
        Load a full analyze request from a dictionary.

        Args:
            data: Dictionary containing request data.

        Returns:
            Validated AnalyzeRequest object.

        Raises:
            JsonLoaderError: If data validation fails.
        """
        try:
            return AnalyzeRequest.model_validate(data)
        except Exception as e:
            raise JsonLoaderError(f"Validation error: {e}")

    @staticmethod
    def save_to_file(
        topology: ServiceTopology,
        file_path: str | Path,
        indent: int = 2,
    ) -> None:
        """
        Save service topology to a JSON file.

        Args:
            topology: The topology to save.
            file_path: Path to the output file.
            indent: JSON indentation level.

        Raises:
            JsonLoaderError: If file cannot be written.
        """
        path = Path(file_path)

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    topology.model_dump(by_alias=True),
                    f,
                    indent=indent,
                    ensure_ascii=False,
                )
        except IOError as e:
            raise JsonLoaderError(f"Cannot write file: {e}")

    @staticmethod
    def to_json_string(
        topology: ServiceTopology,
        indent: int | None = 2,
    ) -> str:
        """
        Convert service topology to a JSON string.

        Args:
            topology: The topology to convert.
            indent: JSON indentation level (None for compact).

        Returns:
            JSON string representation.
        """
        return json.dumps(
            topology.model_dump(by_alias=True),
            indent=indent,
            ensure_ascii=False,
        )
