from testcontainers.core.container import DockerContainer


class DataEtatPrefectContainer(DockerContainer):
    def __init__(self, exposed_port: int):
        super().__init__("prefecthq/prefect:3.6.6-python3.12")

        self.with_env("PREFECT_API_URL", "http://0.0.0.0:4200/api")
        self.with_env("PREFECT_SERVER_ALLOW_EPHEMERAL_MODE", "true")
        self.with_env("PREFECT_LOGGING_LEVEL", "INFO")

        self.with_bind_ports(4200, exposed_port)

        self.with_command("prefect server start --host 0.0.0.0 --port 4200")

    def get_api_url(self):
        host = self.get_container_host_ip()
        port = self.get_exposed_port(4200)
        return f"http://{host}:{port}/api"
