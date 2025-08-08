"""
Common validation utilities for repositories.

Provides reusable validation logic to eliminate code duplication
following the DRY principle and Single Responsibility Principle.
"""

from typing import Set, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ValidationError(ValueError):
    """Custom exception for validation errors."""

    pass


class FieldValidator:
    """
    Utility class for common field validation patterns.

    Follows Single Responsibility Principle by focusing only on validation logic.
    """

    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any], required_fields: Set[str]
    ) -> None:
        """
        Validate that all required fields are present.

        Args:
            data: Data dictionary to validate
            required_fields: Set of required field names

        Raises:
            ValidationError: If required fields are missing
        """
        if not required_fields.issubset(data.keys()):
            missing = required_fields - data.keys()
            raise ValidationError(f"Missing required fields: {missing}")

    @staticmethod
    def validate_field_presence(
        value: Any, field_name: str, allow_empty: bool = False
    ) -> None:
        """
        Validate that a field has a value.

        Args:
            value: Value to validate
            field_name: Name of the field
            allow_empty: Whether to allow empty strings

        Raises:
            ValidationError: If field is missing or empty when not allowed
        """
        if value is None:
            raise ValidationError(f"Field '{field_name}' is required")

        if isinstance(value, str) and not allow_empty and not value.strip():
            raise ValidationError(f"Field '{field_name}' cannot be empty")

    @staticmethod
    def validate_email_format(email: str) -> None:
        """
        Basic email format validation.

        Args:
            email: Email to validate

        Raises:
            ValidationError: If email format is invalid
        """
        if not email or "@" not in email or "." not in email.split("@")[-1]:
            raise ValidationError("Invalid email format")


class EntityValidator:
    """
    Validator for entity creation patterns.

    Provides common validation logic for repository create methods.
    """

    @staticmethod
    def validate_client_data(**kwargs) -> None:
        """
        Validate client creation data.

        Args:
            **kwargs: Client attributes

        Raises:
            ValidationError: If validation fails
        """
        required_fields = {"user_id", "name", "email"}
        FieldValidator.validate_required_fields(kwargs, required_fields)

        # Additional client-specific validations
        FieldValidator.validate_email_format(kwargs["email"])
        FieldValidator.validate_field_presence(kwargs["name"], "name")

    @staticmethod
    def validate_user_data(**kwargs) -> None:
        """
        Validate user creation data.

        Args:
            **kwargs: User attributes

        Raises:
            ValidationError: If validation fails
        """
        required_fields = {"email"}
        FieldValidator.validate_required_fields(kwargs, required_fields)

        # Additional user-specific validations
        FieldValidator.validate_email_format(kwargs["email"])


def safe_entity_update(entity: Any, **kwargs) -> None:
    """
    Safely update entity attributes.

    Only updates attributes that exist on the entity,
    preventing accidental attribute creation.

    Args:
        entity: Entity to update
        **kwargs: Fields to update
    """
    for key, value in kwargs.items():
        if hasattr(entity, key):
            setattr(entity, key, value)
        else:
            logger.warning(
                f"Attempted to set non-existent attribute '{key}' on {entity.__class__.__name__}"
            )
