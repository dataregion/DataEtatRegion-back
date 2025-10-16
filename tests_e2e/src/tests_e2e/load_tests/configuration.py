import os
import functools


@functools.lru_cache()
def api_base_url():
    api_base = os.getenv("API_BASE_URL", "http://localhost:5000")
    print(f"API_BASE_URL: {api_base}")
    return api_base


@functools.lru_cache()
def keycloak_url():
    url = os.getenv("KEYCLOAK_URL", "http://localhost:8080")
    print(f"KEYCLOAK_URL: {url}")
    return url


@functools.lru_cache()
def keycloak_realm():
    realm = os.getenv("KEYCLOAK_REALM", "test_realm")
    print(f"KEYCLOAK_REALM: {realm}")
    return realm


@functools.lru_cache()
def client_id():
    client = os.getenv("CLIENT_ID", "test_client_id")
    print(f"CLIENT_ID: {client}")
    return client


@functools.lru_cache()
def client_secret():
    secret = os.getenv("CLIENT_SECRET", "test_client_secret")
    print(f"CLIENT_SECRET: {'***' if secret else 'None'}")
    return secret


@functools.lru_cache()
def username():
    user = os.getenv("USERNAME", "test_username")
    print(f"USERNAME: {user}")
    return user


@functools.lru_cache()
def password():
    pwd = os.getenv("PASSWORD", "test_password")
    print(f"PASSWORD: {'***' if pwd else 'None'}")
    return pwd
