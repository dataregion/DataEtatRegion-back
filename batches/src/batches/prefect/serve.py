from prefect import serve
from batches.prefect.exporte_une_recherche import exporte_une_recherche


def main():
    export_recherche_deploiement = exporte_une_recherche.to_deployment(name="exporte_une_recherche")
    serve(
        export_recherche_deploiement,  # type: ignore
    )


if __name__ == "__main__":
    main()
