from flask_sqlalchemy import SQLAlchemy
from models import init as init_persistence_module

db = SQLAlchemy()

init_persistence_module(base=db.Model)
