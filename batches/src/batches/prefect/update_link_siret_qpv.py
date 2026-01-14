from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import zipfile

from models.entities.refs.Siret import Siret
import pandas as pd
from prefect import task, flow, runtime
from prefect.cache_policies import NO_CACHE
from sqlalchemy import bindparam, update

from batches.share.tasks.files import CtxDownloadFile, download_remote_file, should_download
from batches.database import session_scope
from batches.share.tasks.calendar import is_second_day_of_week_in_month


def _print(text: str):
    print(f"[TASK][SIRET_QPV] {text}")


@dataclass
class _CtxTask:

    qpv_colname: str
    ctx_download: CtxDownloadFile
    csv_filename_in_zip: Optional[str]=  None
    chunksize: int = 1000

    current_chunk: int = 1
    current_lines: Optional[pd.DataFrame] = None


@task(timeout_seconds=60, log_prints=True, cache_policy=NO_CACHE)
def get_first_csv_in_zip(ctx: _CtxTask) -> _CtxTask:
    with zipfile.ZipFile(ctx.ctx_download.filename, "r") as zip_file:
        csv_names = [name for name in zip_file.namelist() if name.lower().endswith(".csv")]

        if not csv_names:
            raise RuntimeError("Aucun fichier CSV trouvé dans l'archive")

        if len(csv_names) > 1:
            raise RuntimeError("Plusieurs CSV trouvés alors qu'un seul est attendu")

        # Reset du filename, on va travailler sur le CSV maintenant
        ctx.csv_filename_in_zip = csv_names[0]
    
    return ctx


@task(timeout_seconds=60, log_prints=True, cache_policy=NO_CACHE)
def update_link_siret_qpv(ctx: _CtxTask) -> _CtxTask:
    _print(f"Chunk {ctx.current_chunk} : Update pour {len(ctx.current_lines)} Siret")
    
    siret_qpv_col = "code_qpv24" if ctx.qpv_colname == "plg_qp24" else "code_qpv15"
    with session_scope() as session:
        to_update: list[dict] = []
        for _, row in ctx.current_lines.iterrows():
            to_update.append({"code_siret": row["siret"], siret_qpv_col: row[ctx.qpv_colname]})

        stmt = update(Siret).where(Siret.code == bindparam("code_siret"))
        session.execute(stmt, to_update)

    return ctx


@flow(log_prints=True)
def update_link_siret_qpv_from_url(url: str = "", day_of_week: int = 5, qpv_colname: str = "plg_qp15"):
    
    if not is_second_day_of_week_in_month(day_of_week):
        raise RuntimeError(
            f"Tâche ignorée : aujourd'hui ({datetime.today().date()}) n'est pas le second {day_of_week} du mois."
        )

    ctx_download = CtxDownloadFile(
        task_name= str(runtime.flow_run.flow_name),
        url=url,
        resource_uuid=url.split('/')[-1]    # URL data.gouv.fr : Dernière partie = UUID du fichier
    )

    ctx = _CtxTask(qpv_colname=qpv_colname, ctx_download=ctx_download)

    ctx.ctx_download = should_download(ctx.ctx_download)
    if not ctx.ctx_download.should_download:
        return 
    
    ctx.ctx_download = download_remote_file(ctx.ctx_download)
    if ctx.ctx_download.extension != "zip" or ctx.ctx_download.filename is None:
        raise RuntimeError("Une erreur est survenue, un fichier ZIP aurait du être téléchargé.")
    
    ctx = get_first_csv_in_zip(ctx)

    with zipfile.ZipFile(ctx.ctx_download.filename, "r") as zip_file:
                
        with zip_file.open(ctx.csv_filename_in_zip) as csv_file:

            _print("Extraction des infos du CSV ....")

            chunks = pd.read_csv(
                csv_file,
                header=0,
                usecols=["siret", qpv_colname],
                chunksize=ctx.chunksize,
                sep=";",
                dtype={"siret": str, qpv_colname: str},
            )

            # Parcourir les chunks et filtrer les lignes
            for i, chunk in enumerate(chunks, start=1):
                filtered: Optional[pd.DataFrame] = chunk[~chunk[qpv_colname].isin(["CSZ", "HZ", " ", ""])]

                ctx.current_chunk = i
                ctx.current_lines = filtered
                
                if filtered is None or filtered.empty:
                    _print(f"Chunk {ctx.current_chunk} vide : On passe au suivant")
                    continue
    
                ctx = update_link_siret_qpv(ctx)

            _print("Fin de la mise à jours des liens Siret Qpv.")


if __name__ == "__main__":  # Pour le debug
    update_link_siret_qpv_from_url("https://www.data.gouv.fr/fr/datasets/r/ba6a4e4c-aac6-4764-bbd2-f80ae345afc5", 5, "plg_qp24")
