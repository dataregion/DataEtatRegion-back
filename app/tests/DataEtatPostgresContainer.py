from testcontainers.postgres import PostgresContainer


class DataEtatPostgresContainer(PostgresContainer):
    def __init__(self):
        self.__image_name = "postgres:15.4"
        return super(DataEtatPostgresContainer, self).__init__(image=self.__image_name)

    def get_connection_url(self, host=None):
        return super()._create_connection_url(
            dialect="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            db_name=self.POSTGRES_DB,
            host=host,
            port=self.port_to_expose,
        )
