# analysis.py
#
# This module contains functions for analyzing and modifying results that have
# been previously stored in an spdxSummarizer database. It is intended to be
# used by the reports.py functions, for analyzing and modifying results just
# prior to generating reports, but _not_ for making changes that will be saved
# into the database itself.
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

import os.path

# Modify a category/license/filename dict so that "No license found" files
# with extensions in the "ignore_extensions" list are separately designated.
# Keep the category the same, but change the license to "No license found -
# excluded file extension". Also adjust the corresponding license count values.
# arguments:
#   1) FTDatabase
#   2) dict of category =>
#       (category_name, {filename => license}, {license => count})
#      typically created by dbtools.getCategoryFilesForScan()
# returns: True if successfully modified category dict, False on error
def analyzeFileExtensions(db, cats):
  old_license_title = "No license found"
  new_license_title = "No license found - excluded file extension"

  # first, see if we've even got a "No license found" category
  cat = None
  for cat_id, cat_tuple in cats.items():
    cname = cat_tuple[0]
    if cname == old_license_title:
      cat = cat_tuple
      break
  if not cat:
    print(f"Didn't find category called \"{old_license_title}\"; not analyzing for excluded file extensions.")
    return False

  category_name = cat[0]
  category_filenames = cat[1]
  license_counts = cat[2]

  # get and parse the list of ignored extensions from config
  ignored_extensions_str = db.getConfigForKey("ignore_extensions")
  if not ignored_extensions_str:
    print(f"Couldn't get list of ignored extensions from database config.")
    return False
  ignored_extensions = ignored_extensions_str.split(';')

  # now, walk through each filename and check its extension against the
  # list of ignored extensions. ignore any licenses that are different
  # from old_license_title (b/c they've probably already been put into
  # a separate category).
  count_changed = 0
  for filename, license in category_filenames.items():
    ext_t = os.path.splitext(filename)
    extension = ext_t[1]
    if license == old_license_title and extension in ignored_extensions:
      count_changed += 1
      category_filenames[filename] = new_license_title

  # finally, update the license counts
  if count_changed > 0:
    license_counts[old_license_title] -= count_changed
    license_counts[new_license_title] = count_changed

  return True

# Modify a filename => license dict so that "No license found" files
# with extensions in the "ignore_extensions" list are separately designated.
# arguments:
#   1) FTDatabase
#   2) dict of filename => license
#      typically created by dbtools.getLicenseAndFilesForScan()
# returns: True if successfully modified dict, False on error
def analyzeFileExtensionsForFlatDict(db, records):
  old_license_title = "No license found"
  new_license_title = "No license found - excluded file extension"

  # get and parse the list of ignored extensions from config
  ignored_extensions_str = db.getConfigForKey("ignore_extensions")
  if not ignored_extensions_str:
    print(f"Couldn't get list of ignored extensions from database config.")
    return False
  ignored_extensions = ignored_extensions_str.split(';')

  # now, walk through each filename and check its extension against the
  # list of ignored extensions. ignore any licenses that are different
  # from old_license_title (b/c they've probably already been put into
  # a separate category).
  for filename, license in records.items():
    ext_t = os.path.splitext(filename)
    extension = ext_t[1]
    if license == old_license_title and extension in ignored_extensions:
      records[filename] = new_license_title

  return True

# Modify a category/license/filename dict so that "No license found" files
# inside a "vendor/" directory are separately designated.
# Keep the category the same, but change the license to "No license found -
# in vendor directory". Also adjust the corresponding license count values.
# arguments:
#   1) FTDatabase
#   2) dict of category =>
#       (category_name, {filename => license}, {license => count})
#      typically created by dbtools.getCategoryFilesForScan()
# returns: True if successfully modified category dict, False on error
def analyzeVendorFiles(db, cats):
  old_license_title = "No license found"
  new_license_title = "No license found - in vendor directory"

  # first, see if we've even got a "No license found" category
  cat = None
  for cat_id, cat_tuple in cats.items():
    cname = cat_tuple[0]
    if cname == old_license_title:
      cat = cat_tuple
      break
  if not cat:
    print(f"Didn't find category called \"{old_license_title}\"; not analyzing for excluded file extensions.")
    return False

  category_name = cat[0]
  category_filenames = cat[1]
  license_counts = cat[2]

  # walk through each filename and check if its path contains "vendor/".
  # ignore any licenses that are different from old_license_title (b/c 
  # they've probably already been put into a separate category).
  count_changed = 0
  for filename, license in category_filenames.items():
    if license == old_license_title and "vendor/" in filename:
      count_changed += 1
      category_filenames[filename] = new_license_title

  # finally, update the license counts
  if count_changed > 0:
    license_counts[old_license_title] -= count_changed
    license_counts[new_license_title] = count_changed

  return True

# Modify a filename => license dict so that "No license found" files
# inside a "vendor/" directory are separately designated.
# arguments:
#   1) FTDatabase
#   2) dict of filename => license
#      typically created by dbtools.getLicenseAndFilesForScan()
# returns: True if successfully modified dict, False on error
def analyzeVendorFilesForFlatDict(db, records):
  old_license_title = "No license found"
  new_license_title = "No license found - in vendor directory"

  # walk through each filename and check if its path contains "vendor/".
  # ignore any licenses that are different
  # from old_license_title (b/c they've probably already been put into
  # a separate category).
  for filename, license in records.items():
    if license == old_license_title and "vendor/" in filename:
      records[filename] = new_license_title

  return True
