#!/bin/bash

# dbMigrate.sh
#
# Launcher script to migrate spdxSummarizer's database to newer or older
# versions. Mostly just a wrapper around alembic's launcher to handle
# the config script and database locations as command-line parameters.
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

# FIXME like spdxSummarizer.sh, this currently assumes that it will be run
# FIXME from the top-level spdxSummarizer directory. Need to figure out a way
# FIXME to have this be definable as part of a Python-packaged installation
# FIXME setup.

CONFIGFILE=./spdxSummarizer/migrations/alembic.ini
DBPATH=$1
shift
alembic -c $CONFIGFILE -x dbname=sqlite:///$DBPATH "$@"
