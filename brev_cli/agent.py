import requests
from pathlib import Path
import os
import shutil
import json
import jose
import logging
import re
import base64
import hashlib
import socket
from http.server import BaseHTTPRequestHandler
from io import BytesIO
import typing
import sys
import subprocess

from . import utils
from .config import config
from . import authentication

logger = logging.getLogger("brev-cli")

dummyCode = """import variables
import shared

def get():
    return {}

"""


class BrevAPI:
    def __init__(self, should_login_callback: typing.Callable, domain=None):
        self.domain = domain if domain is not None else config.api_url
        self.requests = requests
        self.access_key = authentication.Auth().get_access_token(should_login_callback)

    def make_secure_request(self, call, *args, **kwargs):

        header = utils.make_header(self.access_key)

        resp = call(headers=header, *args, **kwargs)
        resp.raise_for_status()

        return resp

    def make_prefixed_domain(self, url):
        if '?' in url:
            return f"{self.domain}/_api/{url}&utm_source=cli"
        else:
            return f"{self.domain}/_api/{url}?utm_source=cli"

    def authenticate(self, email, password):
        url = self.make_prefixed_domain("_auth/login")

        resp = self.requests.post(url, json={"email": email, "password": password})
        resp.raise_for_status()

        return resp.json()

    def get_endpoints(self):
        url = self.make_prefixed_domain("_endpoint")
        resp = self.make_secure_request(self.requests.get, url)
        return resp.json()

    def get_logs(self, type, id):
        url = self.make_prefixed_domain(f"logs?{type}_id={id}")

        resp = self.make_secure_request(self.requests.get, url)

        return resp.json()

    def add_endpoint(self, name, projectID):
        url = self.make_prefixed_domain("_endpoint")

        resp = self.make_secure_request(
            self.requests.post,
            url,
            json={
                "name": name,
                "project_id": projectID,
                "methods": [],
                "code": dummyCode,
            },
        )

        return resp.json()

    def remove_endpoint(self, endpointID):
        url = self.make_prefixed_domain(f"_endpoint/{endpointID}")

        resp = self.make_secure_request(self.requests.delete, url)
        return resp.json()

    def create_project(self, project_name):
        url = self.make_prefixed_domain("_project")
        # resp = self.requests.post(url, json={"name": project_name})
        resp = self.make_secure_request(
            self.requests.post, url, json={"name": project_name}
        )
        resp.raise_for_status()
        return resp.json()

    def get_packages(self, activeProjectID):
        url = self.make_prefixed_domain(f"package?project_id={activeProjectID}")

        resp = self.make_secure_request(self.requests.get, url)
        resp.raise_for_status()

        return resp.json()

    def add_packages(self, activeProjectID, pkg):
        url = self.make_prefixed_domain("package")

        resp = self.make_secure_request(
            self.requests.post, url, json={"name": pkg, "project_id": activeProjectID}
        )
        resp.raise_for_status()

        return resp.json()

    def remove_package(self, pkgID):
        url = self.make_prefixed_domain(f"package/{pkgID}")

        resp = self.make_secure_request(self.requests.delete, url)
        resp.raise_for_status()

        return resp.json()

    def get_variables(self, activeProjectID):
        url = self.make_prefixed_domain(f"variable?project_id={activeProjectID}")

        resp = self.make_secure_request(self.requests.get, url)

        return resp.json()

    def add_variables(self, activeProjectID, name, value):
        url = self.make_prefixed_domain("variable")

        resp = self.make_secure_request(
            self.requests.post,
            url,
            json={"name": name, "value": value, "project_id": activeProjectID},
        )

        return resp.json()

    def remove_variables(self, varID):
        url = self.make_prefixed_domain(f"variable/{varID}")

        resp = self.make_secure_request(self.requests.delete, url)
        resp.raise_for_status()

        return resp.json()

    def get_modules(self):
        url = self.make_prefixed_domain(f"module")
        
        resp = self.make_secure_request(self.requests.get, url)

        return resp.json()

    def update_module(self, module_id, source):
        url = self.make_prefixed_domain(f"/module/{module_id}")
        args = {"source": source}
        resp = self.make_secure_request(self.requests.put, url, json=args)
        return resp.json()

    def update_endpoint(
        self, code=None, name=None, project_id=None, id=None, methods=None, uri=None
    ):
        # args = utils.get_method_args_as_dict(locals(), should_remove_none=True)
        args = {"code": code, "name": name, "methods": methods}
        url = self.make_prefixed_domain(f"_endpoint/{id}")
        resp = self.make_secure_request(self.requests.put, url, json=args)

    def get_projects(self):
        url = self.make_prefixed_domain("_project")

        resp = self.make_secure_request(self.requests.get, url)

        return resp.json()

