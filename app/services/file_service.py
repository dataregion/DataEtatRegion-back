import os
import tempfile
import logging


from werkzeug.utils import secure_filename
from flask import current_app
from app.exceptions.exceptions import InvalidFile, FileNotAllowedException

def allowed_file(filename, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = {'csv'}

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def check_file_and_save(file, allowed_extensions={'csv'}) -> str:
    if file.filename == '':
        raise InvalidFile(message="Pas de fichier")

    if file and allowed_file(file.filename, allowed_extensions):

        filename = secure_filename(file.filename)
        if 'UPLOAD_FOLDER' in current_app.config:
            save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        else:
            save_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(save_path)
        return save_path
    else:
        logging.error(f'[IMPORT] Fichier refusé {file.filename}')
        raise FileNotAllowedException(message=f'le fichier n\'est pas au format {allowed_extensions}')