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


@functools.lru_cache()
def mail_enabled():
    enabled = os.getenv("MAIL_ENABLED", "false").lower() == "true"
    print(f"MAIL_ENABLED: {enabled}")
    return enabled


@functools.lru_cache()
def mail_host():
    host = os.getenv("MAIL_HOST", "in.message-business.com")
    print(f"MAIL_HOST: {host}")
    return host


@functools.lru_cache()
def mail_port():
    port = os.getenv("MAIL_PORT", 465)
    print(f"MAIL_PORT: {port}")
    return int(port)


@functools.lru_cache()
def mail_login():
    login = os.getenv("MAIL_LOGIN", "user@example.com")
    print(f"MAIL_LOGIN: {login}")
    return login


@functools.lru_cache()
def mail_password():
    password = os.getenv("MAIL_PASSWORD", "password")
    print(f"MAIL_PASSWORD: {'***' if password else 'None'}")
    return password


@functools.lru_cache()
def mail_from():
    _from = os.getenv("MAIL_FROM", "")
    print(f"MAIL_FROM: {_from}")
    return _from


@functools.lru_cache()
def mail_to():
    _to = os.getenv("MAIL_TO", "")
    print(f"MAIL_TO: {_to}")
    return _to
