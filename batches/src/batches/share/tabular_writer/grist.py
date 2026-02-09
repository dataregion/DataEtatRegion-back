from dataclasses import dataclass, asdict
import json
from batches.grist import make_grist_api_service, make_or_get_grist_database_service, make_or_get_user_scim_service
from batches.share.tabular_writer.abstract import TabularWriter


from gristcli.models import UserGrist


from datetime import datetime


@dataclass
class _GristInfo:
    docId: str
    columns: list[str]
    tableId: str


class GristTabularWriter(TabularWriter):
    def __init__(self, filep: str, username: str | None) -> None:
        super().__init__(filep, username)
        self._grist_db_service = make_or_get_grist_database_service()
        self._grist_scim_service = make_or_get_user_scim_service()

    def _save_grist_info(self, grist_info: _GristInfo):
        with open(self._filep, "w", encoding="utf-8") as f:
            json.dump(asdict(grist_info), f, ensure_ascii=False, indent=2)

    def _load_grist_info(self):
        with open(self._filep, "r", encoding="utf-8") as f:
            grist_info = json.load(f)
            grist_info = _GristInfo(**grist_info)
        return grist_info

    def _build_new_doc_name(self) -> str:
        now = datetime.now()
        date_formatee = now.strftime("%d/%m/%Y à %H:%M")
        return f"Export budget {date_formatee}"

    def _prepare_grist_context(self):
        # Patch si API SCIM renvoi 500 : user_id = self._grist_db_service.search_userid_by_email(self._username)
        user = self._grist_scim_service.search_user_by_username(self._username)
        user_id = user.user_id if user else None
        if user is None:
            # SI non exist, create user
            print("[GIRST] No. We create users")

            _user = self._grist_scim_service.create_user(
                UserGrist(username=self._username, email=self._username, display_name=self._username)
            )
            user_id = _user.user_id
            print(f"[GIRST] New user create with id {user_id}")

        # Recup token
        print(f"[GRIST] Get Api key for user {self._username}")
        token = self._grist_db_service.get_or_create_api_token(user_id)

        grist_api = make_grist_api_service(token=token)
        print("[GRIST] Retrive token sucess")

        workspaces = grist_api.get_personnal_workspace()
        if len(workspaces) == 0:
            print("[GRIST] L'utilisateur n'a pas de workspace.")
            workspace_id = grist_api.create_workspace("Home")
            print(f"[GRIST] Création workspace Home {workspace_id}")
        else:
            print(f"[GRIST] Récupération du worskpace {workspaces[0].id}")
            workspace_id = workspaces[0].id

        return grist_api, workspace_id

    def write_header(self, header: list[str]) -> None:
        print(f"GristTabularWriter.write_header: {header}")

        super().write_header(header)

        grist_api, workspace_id = self._prepare_grist_context()

        docName = self._build_new_doc_name()
        print(f"[GRIST] Création document {docName} dans le workspace {workspace_id}")
        docId = grist_api.create_doc_on_workspace(workspace_id, docName)
        print(f"[GRIST] Document {docId} créé")

        columns = [{"id": x, "label": x} for x in header]

        print(f"[GRIST] Création table budget dans le doc {docId} avec les colonnes")
        table_id = grist_api.new_table(
            docId,
            "budget",
            cols=columns,
        )

        grist_info = _GristInfo(docId=docId, columns=header, tableId=table_id)
        self._save_grist_info(grist_info)

    def write_rows(self, rows: list) -> None:
        super().write_rows(rows)
        grist_api, _ = self._prepare_grist_context()
        grist_info = self._load_grist_info()
        doc_id = grist_info.docId
        header = grist_info.columns
        table_id = grist_info.tableId

        data = [dict(zip(header, row, strict=True)) for row in rows]

        grist_api.append_records_to_table(doc_id, table_id, data)

    def close(self) -> None:
        return super().close()
