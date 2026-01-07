from dataclasses import asdict, is_dataclass
import json
import typer

from apis.apps.apis_externes.services.data_subventions import data_subventions_client


api_subventions_client_typer = typer.Typer(help="Client data subventions")


@api_subventions_client_typer.command(
    "subventions", help="Récupère les informations de subventions pour un établissement."
)
def get_subvention_pour_etablissement(siret: str):
    subventions = data_subventions_client.get_subventions_pour_etablissement(siret)
    subventions = [asdict(s) if is_dataclass(s) else s for s in subventions]
    output = json.dumps(subventions)
    typer.echo(output)


@api_subventions_client_typer.command("representants_legaux", help="Récupère les représentants légaux")
def representant_legaux_pour_etablissement(siret: str):
    representant_legaux = data_subventions_client.get_representants_legaux_pour_etablissement(siret)
    representant_legaux = [asdict(r) if is_dataclass(r) else r for r in representant_legaux]
    output = json.dumps(representant_legaux)
    typer.echo(output)
