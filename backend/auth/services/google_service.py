import os
from typing import Dict, Tuple, Any
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests
import jwt
import datetime

class GoogleAuthService:
    """
    Service for handling Google OAuth authentication.
    Single responsibility: Managing Google authentication flows.
    """
    def __init__(self, client_secret_path: str, redirect_uri: str, scopes: list, client_id: str, jwt_secret: str):
        """
        Initializes the GoogleService with the provided configuration parameters.
        Args:
            client_secret_path (str): Path to the client secret JSON file for Google OAuth2.
            redirect_uri (str): Redirect URI to be used in the OAuth2 flow.
            scopes (list): List of OAuth2 scopes required for authentication.
            client_id (str): Google OAuth2 client ID.
            jwt_secret (str): Secret key used for encoding and decoding JWT tokens.
        """
        self.client_secret_path = client_secret_path
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        self.client_id = client_id
        self.jwt_secret = jwt_secret

    def get_authorization_url(self) -> Tuple[str, str]:
        flow = self._create_flow()
        auth_url, state = flow.authorization_url(prompt='consent')
        return auth_url, state

    def get_credentials_from_callback(self, authorization_response: str) -> Dict[str, Any]:
        flow = self._create_flow()
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials
        return {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": getattr(credentials, "token_uri", None),
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes,
            "id_token": getattr(credentials, "id_token", None)
        }

    def verify_id_token(self, id_token_value: str) -> Dict[str, Any]:
        if not id_token_value:
            raise ValueError("ID token is missing")
        user_info = id_token.verify_oauth2_token(
            id_token_value,
            requests.Request(),
            self.client_id
        )
        return user_info

    def create_jwt_token(self, user_info: Dict[str, Any]) -> str:
        payload = {
            "sub": user_info.get("email"),
            "name": user_info.get("name"),
            "email": user_info.get("email"),
            "picture": user_info.get("picture"),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def _create_flow(self) -> Flow:
        if not os.path.isfile(self.client_secret_path):
            raise FileNotFoundError(f"Client secret file not found at {self.client_secret_path}")
        return Flow.from_client_secrets_file(
            self.client_secret_path,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )
