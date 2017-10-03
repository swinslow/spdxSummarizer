# versioning.py
#
# This module contains a function used by the Alembic migration scripts to
# update the version info in an spdxSummarizer database's config table.
#
# Copyright (C) 2017 The Linux Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0

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
