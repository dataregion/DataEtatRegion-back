<%!
import re

%>"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
import logging
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}

<%
    from flask import current_app
    bind_names = []
    if current_app.config.get('SQLALCHEMY_BINDS') is not None:
        bind_names = list(current_app.config['SQLALCHEMY_BINDS'].keys())
    else:
        get_bind_names = getattr(current_app.extensions['migrate'].db, 'bind_names', None)
        if get_bind_names:
            bind_names = get_bind_names()
    db_names = [''] + bind_names
%>

## generate an "upgrade_<xyz>() / downgrade_<xyz>()" function
## for each database name in the ini file.

% for db_name in db_names:

def upgrade_${db_name}():
    ${context.get("%s_upgrades" % db_name, "pass")}


def downgrade_${db_name}():
    ${context.get("%s_downgrades" % db_name, "pass")}

% endfor

# ###############################################################################
# Boilerplate
#
def _call(name):
    if name not in globals():
        logging.warning(f"Pas de fonction: '{name}'. la migration sera ignorée")
    else:
        globals()[name]()

def upgrade(engine_name):
    fn_name = f"upgrade_{engine_name}"
    _call(fn_name)

def downgrade(engine_name):
    fn_name = f"downgrade_{engine_name}"
    _call(fn_name)

# ###############################################################################