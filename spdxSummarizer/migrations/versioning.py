from sqlalchemy.sql import table, column
from sqlalchemy import String

config_table = table('config',
  column('key', String),
  column('value', String)
)

def set_version(op, new_version):
  op.execute(
    config_table.update().where(config_table.c.key == "version").\
      values({'value': new_version})
  )
