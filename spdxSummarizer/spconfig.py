# spconfig.py
#
# This module holds configuration values for spdxSummarizer.
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

# current version of spdxSummarizer
SPVERSION = "0.2.2"

# latest version in which database migrations are required
# e.g. if a DB version is newer than this, then it doesn't require
# a migration, even if it's older than the current SPVERSION
SPVERSION_LAST_DB_CHANGE = "0.2.2"

# Get a version tuple from a version string
# arguments:
#   * version_str: version string in "major.minor.point" format
# returns: tuple of (major.minor.point) or None if bad format
def getVersionTuple(version_str):
  if not version_str:
    return None
  vl = version_str.split(".")
  if len(vl) != 3:
    return None
  if not vl[0].isdigit() or not vl[1].isdigit() or not vl[2].isdigit():
    return None
  major = int(vl[0])
  minor = int(vl[1])
  point = int(vl[2])
  return (major, minor, point)

# Compare version tuples.
# arguments:
#   * vt1: (major.minor.point) tuple of first version string
#   * vt2: (major.minor.point) tuple of second version string
# returns: <0 if first version is less than second
#           0 if first version is equal to second
#          >0 if first version is greater than second
def compareVersionTuples(vt1, vt2):
  major_diff = vt1[0] - vt2[0]
  if major_diff != 0:
    return major_diff
  minor_diff = vt1[1] - vt2[1]
  if minor_diff != 0:
    return minor_diff
  point_diff = vt1[2] - vt2[2]
  return point_diff

# Compare version strings.
# arguments:
#   1) vstr1: first version string in "major.minor.point" format
#   2) vstr2: second version string in "major.minor.point" format
# returns: <0 if first version is less than second
#           0 if first version is equal to second
#          >0 if first version is greater than second
def compareVersionStrings(vstr1, vstr2):
  vt1 = getVersionTuple(vstr1)
  vt2 = getVersionTuple(vstr2)
  return compareVersionTuples(vt1, vt2)

# Compare version string with current spdxSummarizer version.
# arguments:
#   * version_str: version string in "major.minor.point" format
# returns: <0 if version is less than current spdxSummarizer version
#           0 if version is equal to current spdxSummarizer version
#          >0 if version is greaterthan current spdxSummarizer version
def compareVersionToCurrent(version_str):
  return compareVersionStrings(version_str, SPVERSION)

# Compare version string with last database change version.
# arguments:
#   * version_str: version string in "major.minor.point" format
# returns: <0 if version is less than last database change version
#           0 if version is equal to last database change version
#          >0 if version is greaterthan last database change version
def compareVersionToLastDatabaseChange(version_str):
  return compareVersionStrings(version_str, SPVERSION_LAST_DB_CHANGE)

##### DB migration version functions

# Given a database, determine whether it needs to be migrated due to
# later changes in spdxSummarizer.
# arguments:
#   1) db: SPDatabase
# returns: True if DB is too old (needs migration); False if not too old;
#   None if error
def isDBTooOld(db):
  db_version_str = db.getConfigForKey("version")
  if not db_version_str:
    print("Error: Couldn't get version string from database")
    return None
  compare_val = compareVersionStrings(db_version_str, SPVERSION_LAST_DB_CHANGE)
  return compare_val < 0

# Given a database, determine whether it is too new to be used with this
# version of spdxSummarizer.
# arguments:
#   1) db: SPDatabase
# returns: True if DB is too new; False if not too new; None if error
def isDBTooNew(db):
  db_version_str = db.getConfigForKey("version")
  if not db_version_str:
    print("Error: Couldn't get version string from database")
    return None
  # comparing against SPVERSION because we're looking at whether or not
  # this database's version is from a future version of spdxSummarizer.
  compare_val = compareVersionStrings(db_version_str, SPVERSION)
  return compare_val > 0
