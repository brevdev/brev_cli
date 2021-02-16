import json
import requests
import jose.jwt
import logging
import re
import base64
import hashlib
import socket
import http.server
import io
import typing
import sys
import subprocess
import os
import pathlib
import urllib.parse
import string
import random
import cotter

from . import config

logger = logging.getLogger("brev-cli")

cotter_jwks_url = "https://www.cotter.app/api/v0/token/jwks"

cotter_token_url = (
    f"https://www.cotter.app/api/v0/token/{config.config.cotter_api_key_id}"
)

brev_home = os.path.join(pathlib.Path.home(), ".brev")

token_path = os.path.join(brev_home, "credentials.json")

port = 8395


class Auth:
    def login(self):
        tokens = do_cotter_authflow_for_tokens()
        TokenManager.store_tokens(tokens)

    def logout(self):
        subprocess.check_call(["rm", "-f", token_path])

    def get_access_token(self, should_login_callback: typing.Callable):
        print("very top")
        try:
            tm = TokenManager()
            token = tm.get_access_token()
            print("about to return")
            return token
        except AuthException as ae:
            print("exception")
            if should_login_callback():
                tokens = do_cotter_authflow_for_tokens()
                TokenManager.store_tokens(tokens)
                return tokens["access_token"]

    def is_logged_in(self):
        try:
            tm = TokenManager()
            tm.get_access_token()
            return True
        except AuthException as ae:
            return False


class AuthException(Exception):
    ...


def do_cotter_authflow_for_tokens():
    script_path = os.path.realpath(__file__)
    success_page = pathlib.Path(script_path).parent.joinpath(
        "success.html"
    )
    response = cotter.login_with_email_link(
        config.config.cotter_api_key_id, port, redirect_page=success_page
    )
    return response["oauth_token"]


class TokenManager:
    def __init__(self):
        self.cotter_pub_key = self._get_pub_key()
        if not os.path.exists(brev_home):
            raise Exception(
                "The Brev home directory does not exist. Please make sure you have initialized the CLI (brev init)"
            )
        if not os.path.exists(token_path):
            raise AuthException("The Brev cli has not yet been authenticated")

    def get_access_token(self):
        print("get_access_token")
        token = self._get_tokens()["access_token"]
        print("Top")
        print(token)
       
        if not self._is_access_token_valid(token):
            print("not valid")
            token = self._refresh_access_token()
        
        return token

    def _get_tokens(self):
        with open(token_path, "r") as f:
            
            token = json.load(f)
            print("bottom")
            print(token)
            return token

    def _is_token_valid(self, token):
    
        try:
            print(config.config.cotter_api_key_id)
            print(self.cotter_pub_key)
            resp = jose.jwt.decode(
                token,
                self.cotter_pub_key,
                algorithms="ES256",
                audience=config.config.cotter_api_key_id,
            )
            
            print("success")
            return True
        except jose.JWTError as je:
            
            logger.info(je)
            return False

    @classmethod
    def _get_pub_key(cls):
        resp = requests.get(cotter_jwks_url)
        data = resp.json()
        public_key = data["keys"][0]
        return public_key

    def _refresh_access_token(self):
        token = self._get_tokens()["refresh_token"]
        try:
            tokens = self._fetch_tokens_by_refresh(token)
            self.store_tokens(tokens)
            return tokens["access_token"]
        except requests.HTTPError as he:
            if he.response.status_code == 400:
                raise AuthException("refresh token is invalid")
            else:
                raise he

    def _is_access_token_valid(self, token):
        # method to monkeypatch for testing
        return self._is_token_valid(token)

    def _fetch_tokens_by_refresh(self, token):
        body = {"grant_type": "refresh_token", "refresh_token": token}
        headers = {"API_KEY_ID": config.config.cotter_api_key_id}
        resp = requests.post(cotter_token_url, json=body, headers=headers)
        resp.raise_for_status()
        return resp.json()

    @classmethod
    def store_tokens(cls, token_data):
        if not os.path.exists(brev_home):
            # create Brev home
            os.mkdir(brev_home)
        with open(token_path, "w") as f:
            json.dump(token_data, f)
