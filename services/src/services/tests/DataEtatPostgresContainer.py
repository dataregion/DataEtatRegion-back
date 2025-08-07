from testcontainers.postgres import PostgresContainer


class DataEtatPostgresContainer(PostgresContainer):
    def __init__(self):
        self.__image_name = "postgis/postgis:15-3.5"
        return super(DataEtatPostgresContainer, self).__init__(
            image=self.__image_name, driver="psycopg"
        )
