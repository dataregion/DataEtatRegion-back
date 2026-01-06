import typer
import json

from apis.cli.api_externes import api_subventions_client_typer
from apis.config.Config import Config

cli = typer.Typer()


def _config_schema_str():
    model = Config.model_json_schema()
    model_str = json.dumps(model, indent=2)
    return model_str


@cli.command()
def refresh_dev_schemas():
    target = "./config/apis-config.schema.json"
    model_str = _config_schema_str()

    with open(target, "+w") as f:
        f.write(model_str)


@cli.command()
def config_json_schema():
    model_str = _config_schema_str()
    print(model_str)


cli.add_typer(
    api_subventions_client_typer, name="data_subventions_client", help="Client data subvention tel qu'utilisé par apis"
)

if __name__ == "__main__":
    cli()
