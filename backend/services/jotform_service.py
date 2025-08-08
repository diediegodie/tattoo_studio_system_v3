"""
JotForm service layer implementing business logic.

This service follows SOLID principles by:
- Single Responsibility: Only handles JotForm API operations
- Open/Closed: Extensible for new form providers
- Interface Segregation: Focused interface for form operations
"""

import requests
from typing import List, Dict, Any, Optional, Protocol
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class FormProvider(Protocol):
    """
    Protocol for form providers following Interface Segregation Principle.

    Defines minimal interface that any form provider must implement.
    """

    def get_forms(self) -> Optional[List[Dict[str, Any]]]:
        """Get all forms."""
        ...

    def get_submissions(self, form_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get submissions for a form."""
        ...


class BaseFormService(ABC):
    """
    Abstract base class for form services.

    Follows Open/Closed Principle - new form providers
    can extend this without modifying existing code.
    """

    def __init__(self, api_key: str):
        """
        Initialize form service.

        Args:
            api_key: API key for the form service
        """
        self.api_key = api_key

    @abstractmethod
    def get_forms(self) -> Optional[List[Dict[str, Any]]]:
        """Get all forms from the provider."""
        pass

    @abstractmethod
    def get_submissions(self, form_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get submissions for a specific form."""
        pass

    @abstractmethod
    def parse_client_data(self, submission: Dict[str, Any]) -> Dict[str, str]:
        """Parse client data from a submission."""
        pass


class JotFormService(BaseFormService):
    """
    JotForm API service implementation.

    Implements specific JotForm API operations while following
    Liskov Substitution Principle - can be substituted for BaseFormService.
    """

    BASE_URL = "https://api.jotform.com"
    REQUEST_TIMEOUT = 10

    def __init__(self, api_key: str):
        """
        Initialize JotForm service.

        Args:
            api_key: JotForm API key

        Raises:
            ValueError: If API key is empty
        """
        if not api_key or not api_key.strip():
            raise ValueError("JotForm API key cannot be empty")

        super().__init__(api_key)
        logger.info("JotForm service initialized")

    def get_submissions(self, form_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get submissions for a JotForm form.

        Args:
            form_id: JotForm form ID

        Returns:
            Optional[List[Dict]]: List of submissions or None if error
        """
        if not form_id or not form_id.strip():
            logger.warning("Form ID cannot be empty")
            return None

        url = f"{self.BASE_URL}/form/{form_id}/submissions"
        params = {"apiKey": self.api_key}

        try:
            logger.info(f"Fetching submissions for form {form_id}")
            response = requests.get(url, params=params, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()

            data = response.json()
            submissions = data.get("content", [])

            logger.info(f"Retrieved {len(submissions)} submissions for form {form_id}")
            return submissions

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching submissions for form {form_id}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching submissions for form {form_id}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching submissions for form {form_id}: {e}")
            return None
        except ValueError as e:
            logger.error(f"JSON decode error for form {form_id}: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error fetching submissions for form {form_id}: {e}"
            )
            return None

    def get_forms(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get all forms for the user.

        Returns:
            Optional[List[Dict]]: List of forms or None if error
        """
        url = f"{self.BASE_URL}/user/forms"
        params = {"apiKey": self.api_key}

        try:
            logger.info("Fetching user forms")
            response = requests.get(url, params=params, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()

            data = response.json()
            forms = data.get("content", [])

            logger.info(f"Retrieved {len(forms)} forms")
            return forms

        except requests.exceptions.Timeout:
            logger.error("Timeout fetching user forms")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching user forms: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching user forms: {e}")
            return None
        except ValueError as e:
            logger.error(f"JSON decode error fetching user forms: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching user forms: {e}")
            return None

    def parse_client_data(self, submission: Dict[str, Any]) -> Dict[str, str]:
        """
        Parse client data from a JotForm submission.

        Args:
            submission: JotForm submission data

        Returns:
            Dict[str, str]: Parsed client data with keys: name, email, phone
        """
        client_data = {"name": "", "email": "", "phone": ""}

        try:
            answers = submission.get("answers", {})

            for answer in answers.values():
                if not isinstance(answer, dict):
                    continue

                question_type = answer.get("type", "")

                if question_type == "control_fullname":
                    client_data["name"] = answer.get("prettyFormat", "").strip()
                elif question_type == "control_email":
                    client_data["email"] = answer.get("answer", "").strip()
                elif question_type == "control_phone":
                    client_data["phone"] = answer.get("prettyFormat", "").strip()

            logger.debug(f"Parsed client data: {client_data}")
            return client_data

        except Exception as e:
            logger.error(f"Error parsing client data from submission: {e}")
            return client_data

    def get_clients_from_first_form(self) -> Optional[List[Dict[str, str]]]:
        """
        Get client data from the first form's submissions.

        Returns:
            Optional[List[Dict]]: List of client data or None if error
        """
        try:
            forms = self.get_forms()
            if not forms:
                logger.warning("No forms found")
                return None

            first_form = forms[0]
            form_id = first_form.get("id")

            if not form_id:
                logger.warning("First form has no ID")
                return None

            logger.info(f"Getting clients from first form: {form_id}")
            submissions = self.get_submissions(form_id)

            if not submissions:
                logger.info("No submissions found in first form")
                return []

            clients = []
            for submission in submissions:
                client_data = self.parse_client_data(submission)

                # Only add clients with at least name or email
                if client_data["name"] or client_data["email"]:
                    clients.append(client_data)

            logger.info(f"Parsed {len(clients)} clients from first form")
            return clients

        except Exception as e:
            logger.error(f"Error getting clients from first form: {e}")
            return None

    def validate_api_key(self) -> bool:
        """
        Validate the API key by making a test request.

        Returns:
            bool: True if API key is valid
        """
        try:
            forms = self.get_forms()
            return forms is not None
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return False


class FormServiceFactory:
    """
    Factory for creating form services.

    Follows Dependency Inversion Principle by providing
    abstraction for service creation.
    """

    @staticmethod
    def create_jotform_service(api_key: str) -> JotFormService:
        """
        Create JotForm service instance.

        Args:
            api_key: JotForm API key

        Returns:
            JotFormService: JotForm service instance
        """
        return JotFormService(api_key)

    @staticmethod
    def create_form_service(provider: str, api_key: str) -> BaseFormService:
        """
        Create form service based on provider.

        Args:
            provider: Provider name (currently only 'jotform')
            api_key: API key for the provider

        Returns:
            BaseFormService: Form service instance

        Raises:
            ValueError: If provider is not supported
        """
        providers = {
            "jotform": JotFormService,
        }

        provider_class = providers.get(provider.lower())
        if not provider_class:
            raise ValueError(f"Unsupported provider: {provider}")

        return provider_class(api_key)
