from brev_cli import __version__
import os
import subprocess
import pathlib
import pytest
import json
import requests
import unittest.mock

from brev_cli import authentication


def test_version():
    assert __version__ == "0.1.4"


def get_brev_creds_path():
    brev_creds = pathlib.Path.home()
    path = os.path.join(brev_creds, ".brev/credentials.json")
    return path


def delete_credentials():
    path = get_brev_creds_path()
    subprocess.check_call(["rm", "-rf", path])


@pytest.fixture
def clean_credentials():
    delete_credentials()
    yield
    delete_credentials()


@pytest.fixture
def with_credentials():
    with open(get_brev_creds_path(), mode="w") as file:
        json.dump(init_tokens, file)
    yield init_tokens
    delete_credentials()


@pytest.fixture
def access_token_is_valid(monkeypatch):
    def _is_access_token_valid(self, token):
        return True

    monkeypatch.setattr(
        authentication.TokenManager, "_is_access_token_valid", _is_access_token_valid
    )
    yield


@pytest.fixture
def access_token_is_invalid(monkeypatch):
    def _is_access_token_valid(self, token):
        return False

    monkeypatch.setattr(
        authentication.TokenManager, "_is_access_token_valid", _is_access_token_valid
    )
    yield


@pytest.fixture
def refresh_token_is_valid(monkeypatch):
    def refresh_access(self, token):
        return refresh_response_tokens

    monkeypatch.setattr(
        authentication.TokenManager, "_fetch_tokens_by_refresh", refresh_access
    )
    yield refresh_response_tokens


@pytest.fixture
def refresh_token_is_invalid(monkeypatch):
    def refresh_access(self, token):
        resp = unittest.mock.Mock(spec=requests.Response)
        resp.status_code = 400
        raise requests.HTTPError(response=resp)

    monkeypatch.setattr(
        authentication.TokenManager, "_fetch_tokens_by_refresh", refresh_access
    )
    yield


@pytest.fixture
def cotter_auth_flow_tokens(monkeypatch):
    def get_token():
        return fresh_login_resp

    monkeypatch.setattr(authentication, "do_cotter_authflow_for_tokens", get_token)
    yield fresh_login_resp


def test_get_access_token_no_creds_file(clean_credentials, cotter_auth_flow_tokens):
    token = authentication.Auth().get_access_token(lambda: True)
    assert token == cotter_auth_flow_tokens["access_token"]


def test_get_access_token_existing(with_credentials, access_token_is_valid):
    token = authentication.Auth().get_access_token(lambda: True)
    assert token == with_credentials["access_token"]


def test_access_key_invalid(
    with_credentials,
    cotter_auth_flow_tokens,
    access_token_is_invalid,
    refresh_token_is_valid,
):
    token = authentication.Auth().get_access_token(lambda: True)
    assert token == refresh_token_is_valid["access_token"]


def test_get_access_refresh_key_invalid(
    with_credentials,
    cotter_auth_flow_tokens,
    refresh_token_is_invalid,
    access_token_is_invalid,
):
    token = authentication.Auth().get_access_token(lambda: True)
    assert token == cotter_auth_flow_tokens["access_token"]


fresh_login_resp = {
    "access_token": "eyJhbGciOiJFUzI1NiIsImtpZCI6IlNQQUNFX0pXVF9QVUJMSUM6ODAyOEFBQTMtRUMyRC00QkFBLUJFN0EtN0M4MzU5Q0NCOUY5IiwidHlwIjoiSldUIn0.eyJjbGllbnRfdXNlcl9pZCI6ImVlMTk4MmU5LTE1OTYtNDFkYi1iMWExLTRjMTg4MGMxZjAxNiIsImF1dGhlbnRpY2F0aW9uX21ldGhvZCI6Ik9UUCIsInR5cGUiOiJjbGllbnRfYWNjZXNzX3Rva2VuIiwic2NvcGUiOiJhY2Nlc3MiLCJhdWQiOiIxOTAyNDc2Ny1hMGIyLTQyMjEtOGZhYS1lZjExNmRjODUzZDAiLCJleHAiOjE1OTgxMzI2OTIsImp0aSI6IjkwMTUyOGYzLWQ0YjUtNGQzZi1hNWE3LWIxMWU3ZDkyOGFjYiIsImlhdCI6MTU5ODEyOTA5MiwiaXNzIjoiaHR0cHM6Ly93d3cuY290dGVyLmFwcCIsInN1YiI6ImVlMTk4MmU5LTE1OTYtNDFkYi1iMWExLTRjMTg4MGMxZjAxNiJ9.cuvbbWlujyZIQpg84ORYaA2pmu7tGFaK58lbfTt-Gs5lICw1aXsJm6xPyKDHKm-kM8kNekYalQrtwKrDV628xg",
    "id_token": "eyJhbGciOiJFUzI1NiIsImtpZCI6IlNQQUNFX0pXVF9QVUJMSUM6ODAyOEFBQTMtRUMyRC00QkFBLUJFN0EtN0M4MzU5Q0NCOUY5IiwidHlwIjoiSldUIn0.eyJjbGllbnRfdXNlcl9pZCI6ImVlMTk4MmU5LTE1OTYtNDFkYi1iMWExLTRjMTg4MGMxZjAxNiIsImF1dGhfdGltZSI6Ii02MjEzNTU5NjgwMCIsImlkZW50aWZpZXIiOiJhbGVjZm9uZzFAZ21haWwuY29tIiwidHlwZSI6ImNsaWVudF9pZF90b2tlbiIsImF1ZCI6IjE5MDI0NzY3LWEwYjItNDIyMS04ZmFhLWVmMTE2ZGM4NTNkMCIsImV4cCI6MTU5ODEzMjY5MiwianRpIjoiMzEyZDMyZDEtOTQ3Yi00NmFiLTg0OGMtYTEyYTU5Mjc1NTY1IiwiaWF0IjoxNTk4MTI5MDkyLCJpc3MiOiJodHRwczovL3d3dy5jb3R0ZXIuYXBwIiwic3ViIjoiZWUxOTgyZTktMTU5Ni00MWRiLWIxYTEtNGMxODgwYzFmMDE2In0.J150vbA5jSYW6Og8mCclG5Cb41JzRJHbZmKRVo-WwD_oMDWY7HPI7G6KdPHrUjpSiB6iKu1Tc_aaj3Q6vQ6p9Q",
    "refresh_token": "39560:XSMAWf1c3NPutqJzmzdHO6UMStrx9tzWelUnLZeBqcCtbmBJaH",
    "expires_in": 3600,
    "token_type": "Bearer",
    "auth_method": "OTP",
}

init_tokens = {
    "access_token": "xxxxbGciOiJFUzI1NiIsImtpZCI6IlNQQUNFX0pXVF9QVUJMSUM6ODAyOEFBQTMtRUMyRC00QkFBLUJFN0EtN0M4MzU5Q0NCOUY5IiwidHlwIjoiSldUIn0.eyJjbGllbnRfdXNlcl9pZCI6ImVlMTk4MmU5LTE1OTYtNDFkYi1iMWExLTRjMTg4MGMxZjAxNiIsImF1dGhlbnRpY2F0aW9uX21ldGhvZCI6Ik9UUCIsInR5cGUiOiJjbGllbnRfYWNjZXNzX3Rva2VuIiwic2NvcGUiOiJhY2Nlc3MiLCJhdWQiOiIxOTAyNDc2Ny1hMGIyLTQyMjEtOGZhYS1lZjExNmRjODUzZDAiLCJleHAiOjE1OTgxMzI2OTIsImp0aSI6IjkwMTUyOGYzLWQ0YjUtNGQzZi1hNWE3LWIxMWU3ZDkyOGFjYiIsImlhdCI6MTU5ODEyOTA5MiwiaXNzIjoiaHR0cHM6Ly93d3cuY290dGVyLmFwcCIsInN1YiI6ImVlMTk4MmU5LTE1OTYtNDFkYi1iMWExLTRjMTg4MGMxZjAxNiJ9.cuvbbWlujyZIQpg84ORYaA2pmu7tGFaK58lbfTt-Gs5lICw1aXsJm6xPyKDHKm-kM8kNekYalQrtwKrDV628xg",
    "id_token": "xxxxbGciOiJFUzI1NiIsImtpZCI6IlNQQUNFX0pXVF9QVUJMSUM6ODAyOEFBQTMtRUMyRC00QkFBLUJFN0EtN0M4MzU5Q0NCOUY5IiwidHlwIjoiSldUIn0.eyJjbGllbnRfdXNlcl9pZCI6ImVlMTk4MmU5LTE1OTYtNDFkYi1iMWExLTRjMTg4MGMxZjAxNiIsImF1dGhfdGltZSI6Ii02MjEzNTU5NjgwMCIsImlkZW50aWZpZXIiOiJhbGVjZm9uZzFAZ21haWwuY29tIiwidHlwZSI6ImNsaWVudF9pZF90b2tlbiIsImF1ZCI6IjE5MDI0NzY3LWEwYjItNDIyMS04ZmFhLWVmMTE2ZGM4NTNkMCIsImV4cCI6MTU5ODEzMjY5MiwianRpIjoiMzEyZDMyZDEtOTQ3Yi00NmFiLTg0OGMtYTEyYTU5Mjc1NTY1IiwiaWF0IjoxNTk4MTI5MDkyLCJpc3MiOiJodHRwczovL3d3dy5jb3R0ZXIuYXBwIiwic3ViIjoiZWUxOTgyZTktMTU5Ni00MWRiLWIxYTEtNGMxODgwYzFmMDE2In0.J150vbA5jSYW6Og8mCclG5Cb41JzRJHbZmKRVo-WwD_oMDWY7HPI7G6KdPHrUjpSiB6iKu1Tc_aaj3Q6vQ6p9Q",
    "refresh_token": "39560:XSMAWf1c3NPutqJzmzdHO6UMStrx9tzWelUnLZeBqcCtbmBJaH",
    "expires_in": 3600,
    "token_type": "Bearer",
    "auth_method": "OTP",
}

refresh_response_tokens = {
    "access_token": "blingblongbGciOiJFUzI1NiIsImtpZCI6IlNQQUNFX0pXVF9QVUJMSUM6ODAyOEFBQTMtRUMyRC00QkFBLUJFN0EtN0M4MzU5Q0NCOUY5IiwidHlwIjoiSldUIn0.eyJjbGllbnRfdXNlcl9pZCI6ImVlMTk4MmU5LTE1OTYtNDFkYi1iMWExLTRjMTg4MGMxZjAxNiIsImF1dGhlbnRpY2F0aW9uX21ldGhvZCI6Ik9UUCIsInR5cGUiOiJjbGllbnRfYWNjZXNzX3Rva2VuIiwic2NvcGUiOiJhY2Nlc3MiLCJhdWQiOiIxOTAyNDc2Ny1hMGIyLTQyMjEtOGZhYS1lZjExNmRjODUzZDAiLCJleHAiOjE1OTgxNDI2MDQsImp0aSI6IjViNDk5NDhiLTAzYmItNGMwZS1iNzFkLTU4MGYxYzQzMThjMCIsImlhdCI6MTU5ODEzOTAwNCwiaXNzIjoiaHR0cHM6Ly93d3cuY290dGVyLmFwcCIsInN1YiI6ImVlMTk4MmU5LTE1OTYtNDFkYi1iMWExLTRjMTg4MGMxZjAxNiJ9.CauEWwG92TM2Snv8utGF9bxpz1VRTXnOrfuYyGCSTNk_qHcxYjIMFfV0XT01c3pYg7MGkeK6Yq2rvJzpc58Aiw",
    "id_token": "eyJhbGciOiJFUzI1NiIsImtpZCI6IlNQQUNFX0pXVF9QVUJMSUM6ODAyOEFBQTMtRUMyRC00QkFBLUJFN0EtN0M4MzU5Q0NCOUY5IiwidHlwIjoiSldUIn0.eyJjbGllbnRfdXNlcl9pZCI6ImVlMTk4MmU5LTE1OTYtNDFkYi1iMWExLTRjMTg4MGMxZjAxNiIsImF1dGhfdGltZSI6Ii02MjEzNTU5NjgwMCIsImlkZW50aWZpZXIiOiJhbGVjZm9uZzFAZ21haWwuY29tIiwidHlwZSI6ImNsaWVudF9pZF90b2tlbiIsImF1ZCI6IjE5MDI0NzY3LWEwYjItNDIyMS04ZmFhLWVmMTE2ZGM4NTNkMCIsImV4cCI6MTU5ODE0MjYwNCwianRpIjoiZDdmMTNiNTAtMTkzNS00YzJhLWJiM2EtNDQ2MmZlOWU3YWZlIiwiaWF0IjoxNTk4MTM5MDA0LCJpc3MiOiJodHRwczovL3d3dy5jb3R0ZXIuYXBwIiwic3ViIjoiZWUxOTgyZTktMTU5Ni00MWRiLWIxYTEtNGMxODgwYzFmMDE2In0.9jpGcb7qRKCA0imm7vkuE3iXc128qg5bs3S5JA-Wv-8SgNPbP5FPi1DnfYonYcwtGcUcVDsSu4-jFzU8eJx3aw",
    "refresh_token": "39560:951xd5AgT8CQz3ftBVTstkMA7YzNz8CzRqernKUnD4DE25Blid",
    "expires_in": 3600,
    "token_type": "Bearer",
    "auth_method": "OTP",
}
