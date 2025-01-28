# deprecated - FileWatcher Depafi. Replace by controller app

import logging
import os
import shutil
import time
import hashlib
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler
from app import create_app_base
from app.files_watchers.tasks_delayer import delay_import_fichier_nat, delay_raise_watcher_exception

logger = logging.getLogger(__name__)
app = create_app_base(expose_endpoint=False, oidc_enable=False, init_celery=True)

# Charger la configuration et gérer les cas où elle est absente
config = app.config.get("FICHIER_NATIONAL_WATCHER", {})

# Gérer les valeurs manquantes avec des valeurs par défaut
timeout = config.get("TEMPS_ATTENTE_FIN_ECRITURE", 10)  # Valeur par défaut de 10 secondes
interval = config.get("INTERVAL", 1)  # Valeur par défaut de 1 seconde
max_growth_time = config.get("MAX_GROWTH_TIME", 3600)  # Valeur par défaut de 1 h
path_to_watch = config.get("PATH_TO_WATCH")
path_a_importer = config.get("PATH_A_IMPORTER")

logger.info(
    f"Démarrage watcher fichier national - path_to_watch : {path_to_watch}, TEMPS_ATTENTE_FIN_ECRITURE : {timeout}, INTERVAL : {interval}, max_growth_time: {max_growth_time}"
)
if not path_to_watch:
    logger.error("La variable PATH_TO_WATCH n'est pas dans la config.")
    exit(1)

# Créer le répertoire A_IMPORTER s'il n'existe pas
if not os.path.exists(path_a_importer):
    os.makedirs(path_a_importer)
    logger.info(f"Répertoire créé : {path_a_importer}")


class FileCreatedHandler(FileSystemEventHandler):

    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            file_name = os.path.basename(file_path)  # Obtenir uniquement le nom du fichier
            logger.info(f"Fichier créé: {file_path}")

            # Traiter uniquement les fichiers CSV et MD5
            if file_name.endswith(".csv") and (file_name.startswith("dp_") or file_name.startswith("ej_")):
                logger.info(f"Fichier CSV détecté: {file_path}")
                self.handle_csv_file(file_path)
            elif file_name.endswith(".md5"):
                logger.info(f"Fichier MD5 détecté: {file_path}")
                self.handle_md5_file(file_path)
            else:
                logger.info(f"Fichier non pris en charge : {file_path}")

    def handle_csv_file(self, csv_path):
        """Gérer la détection d'un fichier CSV et attendre qu'il soit complètement écrit."""
        self.wait_for_file_to_finish_writing(csv_path)
        # Vérifier la présence du fichier MD5 correspondant
        md5_path = f"{csv_path}.md5"
        if os.path.exists(md5_path):
            logger.info(f"Le fichier MD5 correspondant est présent: {md5_path}")
            self.wait_for_file_to_finish_writing(md5_path)
            # Si les deux fichiers sont présents, vérifier l'intégrité et déclencher l'import
            self.verify_and_import(csv_path, md5_path)
        else:
            logger.info(f"Le fichier MD5 pour {csv_path} n'est pas encore disponible. En attente.")

    def handle_md5_file(self, md5_path):
        """Gérer la détection d'un fichier MD5 et attendre qu'il soit complètement écrit."""
        self.wait_for_file_to_finish_writing(md5_path)
        # Une fois le MD5 terminé, vérifier la présence du CSV
        csv_path = md5_path[:-4]  # Retirer le .md5 pour obtenir le chemin du fichier CSV correspondant
        file_name = os.path.basename(csv_path)  # Obtenir le nom du fichier CSV
        if os.path.exists(csv_path) and (file_name.startswith("dp_") or file_name.startswith("ej_")):
            logger.info(f"Le fichier CSV correspondant est présent: {csv_path}")
            self.wait_for_file_to_finish_writing(csv_path)
            # Si les deux fichiers sont écrits, vérifier l'intégrité et déclencher l'import
            self.verify_and_import(csv_path, md5_path)
        else:
            logger.info(f"Le fichier CSV pour {md5_path} n'est pas encore disponible. En attente.")

    def wait_for_file_to_finish_writing(self, file_path):
        """Vérifie si le fichier a cessé de croître en taille (fin d'écriture)"""
        last_size = -1
        stable_size_count = 0
        time_spent_growing = 0  # Initialisation du temps de croissance

        while stable_size_count < timeout:
            try:
                current_size = os.path.getsize(file_path)

                if current_size != last_size:
                    last_size = current_size
                    stable_size_count = 0
                    time_spent_growing += interval
                else:
                    stable_size_count += 1

                logger.info(
                    f"time_spent_growing {time_spent_growing}, max_growth_time {max_growth_time}, current_size {current_size}"
                )

                # Si le fichier continue de croître au-delà du délai maximal
                if time_spent_growing >= max_growth_time:
                    error_message = f"Délai maximal d'écriture dépassé pour le fichier {file_path}. max_growth_time : {max_growth_time}, current_size : {current_size}"
                    delay_raise_watcher_exception(error_message)
                    break

                # Si le fichier a cessé de croître
                if stable_size_count >= timeout:
                    logger.info(f"Le fichier {file_path} a fini d'être écrit.")
                    break

                time.sleep(interval)
            except FileNotFoundError:
                logger.error(f"Le fichier {file_path} n'existe plus.")
                break
            except Exception as e:
                logger.error(f"Erreur lors de la vérification du fichier: {e}")
                break

    def verify_and_import(self, csv_path, md5_path):
        """Vérifier l'intégrité du CSV en comparant son empreinte MD5 avec le fichier MD5"""
        logger.info(f"Vérification de l'intégrité du fichier {csv_path} avec {md5_path}")
        calculated_md5 = self.calculate_md5(csv_path)
        expected_md5 = self.read_md5_file(md5_path)

        if calculated_md5 == expected_md5:
            logger.info(f"L'intégrité du fichier {csv_path} est confirmée. MD5 correspond.")
            new_csv_path = self.move_files_to_importer(csv_path, md5_path)

            # Identifier les fichiers AE et CP à importer
            file_name = os.path.basename(new_csv_path)
            if file_name.startswith("ej_"):
                ae_path = new_csv_path
                cp_path = new_csv_path.replace("ej_", "dp_")
            else:
                cp_path = new_csv_path
                ae_path = new_csv_path.replace("dp_", "ej_")

            # Vérifier si les deux fichiers sont présents avant de lancer l'import
            if os.path.exists(cp_path) and os.path.exists(ae_path):
                delay_import_fichier_nat(ae_path, cp_path)
            else:
                logger.info("En attente du deuxième fichier pour lancer l'import.")
        else:
            error_message = f"L'intégrité du fichier {csv_path} a échoué. MD5 calculé : {calculated_md5}, MD5 attendu : {expected_md5}"
            delay_raise_watcher_exception(error_message)

    def calculate_md5(self, file_path):
        """Calculer l'empreinte MD5 d'un fichier"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Erreur lors du calcul du MD5 pour {file_path}: {e}")
            return None

    def read_md5_file(self, md5_path):
        """Lire l'empreinte MD5 attendue à partir du fichier MD5, en ne prenant que l'empreinte."""
        try:
            with open(md5_path, "r") as f:
                # Récupérer uniquement la première partie avant l'espace ou le nom de fichier
                return f.read().strip().split()[0]
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier MD5 {md5_path}: {e}")
            return None

    def move_files_to_importer(self, csv_path, md5_path):
        """Déplacer le fichier CSV et son MD5 vers le répertoire A_IMPORTER"""
        try:
            # Déplacer le fichier CSV
            csv_filename = os.path.basename(csv_path)
            new_csv_path = os.path.join(path_a_importer, csv_filename)
            shutil.move(csv_path, new_csv_path)
            logger.info(f"Fichier CSV déplacé vers {new_csv_path}")

            # Déplacer le fichier MD5
            md5_filename = os.path.basename(md5_path)
            new_md5_path = os.path.join(path_a_importer, md5_filename)
            shutil.move(md5_path, new_md5_path)
            logger.info(f"Fichier MD5 déplacé vers {new_md5_path}")
            return new_csv_path
        except Exception as e:
            logger.error(f"Erreur lors du déplacement des fichiers {csv_path} et {md5_path}: {e}")
            return None

    def process_existing_files(self, path):
        """Traiter les fichiers existants dans le dossier au démarrage, du plus ancien au plus récent"""
        files = []
        for root, dirs, file_names in os.walk(path):
            for file in file_names:
                file_path = os.path.join(root, file)
                file_name = os.path.basename(file_path)
                # Ajouter les fichiers à la liste avec leur date de modification
                if file_name.startswith("dp_") or file_name.startswith("ej_"):
                    files.append((file_path, os.path.getmtime(file_path)))

        # Trier les fichiers par date de modification (du plus ancien au plus récent)
        files.sort(key=lambda x: x[1])

        # Traiter chaque fichier
        for file_path, _ in files:
            if file_path.endswith(".csv"):
                logger.info(f"Traitement du fichier CSV existant : {file_path}")
                self.handle_csv_file(file_path)


if __name__ == "__main__":
    event_handler = FileCreatedHandler()

    # Traiter les fichiers déjà présents dans le dossier au démarrage (du plus ancien au plus récent)
    event_handler.process_existing_files(path_to_watch)

    # Configuration du système de surveillance de fichiers
    observer = PollingObserver()
    observer.schedule(event_handler, path=path_to_watch, recursive=False)
    observer.start()
    logger.info(f"Surveillance du dossier: {path_to_watch}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    except Exception as e:
        logger.error(f"Erreur lors de la surveillance du dossier: {e}")

    observer.join()
