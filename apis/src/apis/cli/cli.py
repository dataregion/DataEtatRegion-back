import json
from pathlib import Path

import typer

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


@cli.command("antivirus_scan", help="Lance un scan antivirus local via services.antivirus.AntivirusService")
def antivirus_scan(
    file_path: Path = typer.Argument(..., exists=True, file_okay=True, dir_okay=False, readable=True),
    host: str | None = typer.Option(None, "--host", help="Hôte clamd (fallback config APIS)"),
    port: int | None = typer.Option(None, "--port", help="Port clamd (fallback config APIS)"),
    timeout: int | None = typer.Option(None, "--timeout", help="Timeout en secondes (fallback config APIS)"),
    max_file_size_bytes: int | None = typer.Option(
        None,
        "--max-file-size-bytes",
        help="Taille max fichier en octets (fallback config APIS)",
    ),
):
    from apis.config.current import get_config
    from services.antivirus import AntivirusScanError, AntivirusService, VirusFoundError

    config = get_config()
    av_config = config.antivirus

    if av_config is None:
        typer.echo("Configuration antivirus absente dans APIS_CONFIG_PATH")
        raise typer.Exit(code=2)

    resolved_host = host if host is not None else av_config.host
    resolved_port = port if port is not None else av_config.port
    resolved_timeout = timeout if timeout is not None else av_config.timeout
    resolved_max_file_size = max_file_size_bytes if max_file_size_bytes is not None else av_config.max_file_size_bytes

    av_service = AntivirusService(
        host=resolved_host,
        port=resolved_port,
        timeout=resolved_timeout,
        max_file_size_bytes=resolved_max_file_size,
    )

    try:
        av_service.scan_file(
            file_path=str(file_path),
            context={"filename": file_path.name, "source": "cli.antivirus_scan"},
        )
        typer.echo(
            json.dumps(
                {
                    "status": "OK",
                    "message": "Fichier sain",
                    "file": str(file_path),
                }
            )
        )
    except VirusFoundError as e:
        typer.echo(
            json.dumps(
                {
                    "status": "FOUND",
                    "message": "Virus détecté",
                    "virus_name": e.virus_name,
                    "file": str(file_path),
                }
            )
        )
        raise typer.Exit(code=10)
    except AntivirusScanError as e:
        typer.echo(
            json.dumps(
                {
                    "status": "ERROR",
                    "message": e.message,
                    "file": str(file_path),
                }
            )
        )
        raise typer.Exit(code=11)


cli.add_typer(
    api_subventions_client_typer, name="data_subventions_client", help="Client data subvention tel qu'utilisé par apis"
)

if __name__ == "__main__":
    cli()
