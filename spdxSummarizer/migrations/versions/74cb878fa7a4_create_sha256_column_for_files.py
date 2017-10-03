# Database migration scripts are generated using the default script.py.mako
# template from Alembic, which is provided by the upstream author under the
# MIT license:
#
# Copyright (C) 2009-2017 by Michael Bayer.
# Alembic is a trademark of Michael Bayer.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Modifications to the template are provided under the Apache 2.0 license:
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
# SPDX-License-Identifier: Apache-2.0 AND MIT

"""Create SHA256 column for files

Revision ID: 74cb878fa7a4
Revises: 
Create Date: 2017-10-03 15:05:57.425361

"""
from alembic import op
import sqlalchemy as sa

# import version setting function from parent directory
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from versioning import set_version

# Fill in old and new version
NEW_VERSION = "0.2.2"
OLD_VERSION = "0.2.1"

# revision identifiers, used by Alembic.
revision = '74cb878fa7a4'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
  # upgrade to 0.2.2
  op.add_column('files', sa.Column('sha256', sa.String))
  set_version(op, NEW_VERSION)

def downgrade():
  # downgrade to 0.2.1
  with op.batch_alter_table('files') as batch_op:
    batch_op.drop_column('sha256')
  set_version(op, OLD_VERSION)
