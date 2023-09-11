"""This file sets up a command line manager.

Use "python manage.py" for a list of available commands.
Use "python manage.py runserver" to start the development web server on localhost:5000.
Use "python manage.py runserver --help" for a list of runserver options.
"""

from app import create_app_base

app_flask = create_app_base()

if __name__ == "__main__":
    # app_flask.run()

    from app.models.financial.FinancialCp import FinancialCp
    from app.tasks.files.file_task import split_csv_files_and_run_task

    file = "C:\\Users\\jolivetspresta\\Documents\\projects\\SIBSGAR\\referentiels\\2023\\IB53_CP_SGAR_SIMPL_de_01_a_fin_08_2023.csv"
    split_csv_files_and_run_task(
        file,
        "import_file_cp_financial",
        csv_options={
            "sep": ",",
            "skiprows": 8,
            "names": FinancialCp.get_columns_files_cp(),
            "dtype": {
                "programme": str,
                "n_ej": str,
                "n_poste_ej": str,
                "n_dp": str,
                "fournisseur_paye": str,
                "siret": str,
            },
        },
        source_region="053",
        annee=2017,
    )
