# archives.py
#
# This is a collection of functions to compare files originating from a 
# Fossology report with the original files from the zip or tar archive, to 
# aid in identifying any missing files.
#
# NOTE: This module is a work-in-progress and is not currently incorporated
# into the main spdxSummarizer shell.
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

import os
import sys
from zipfile import ZipFile, is_zipfile
from tarfile import TarFile, is_tarfile

from basedata import FileData

# Read a zip file and get its list of files, excluding directories.
# Typically the user shouldn't call this directly, and should just call
#   extract_filename(), which will determine the archive type so that it
#   can call the appropriate extraction helper function.
# arguments:
#   * zip_filename: filename for ZIP formatted archive to be parsed
# returns: list of filename for files contained in the archive, excluding dirs
def extract_filename_from_zip(zip_filename):
  filenames = []
  try:
    with ZipFile(zip_filename, 'r') as z:
      infos = z.infolist()
      filenames = [i.filename for i in infos if not i.is_dir()]
      return filenames
  except (IOError, OSError, FileNotFoundError) as e:
    print(f"Error opening or reading zip archive: {str(e)}")
    return []
  except:
    print("Unexpected error: ", sys.exc_info()[0])
    raise


# Read a tar file and get its list of files, excluding directories.
# Typically the user shouldn't call this directly, and should just call
#   extract_filename(), which will determine the archive type so that it
#   can call the appropriate extraction helper function.
# arguments:
#   * tar_filename: filename for tar-formatted archive (incl. gz) to be parsed
# returns: list of filename for files contained in the archive, excluding dirs
# FIXME note: currently, may need to gunzip a gzip'd tar file BEFORE passing it
# FIXME       to extract_filename_from_tar(), to avoid an InvalidHeaderError
def extract_filename_from_tar(tar_filename):
  filenames = []
  try:
    with TarFile(tar_filename, 'r', encoding="ascii") as t:
      infos = t.getmembers()
      filenames = [i.name for i in infos if i.isfile()]
      return filenames
  except (IOError, OSError, FileNotFoundError) as e:
    print(f"Error opening or reading tar archive: {str(e)}")
    return []
  except:
    print("Unexpected error: ", sys.exc_info()[0])
    raise


# Read an archive file and get its list of files, excluding directories.
# arguments:
#   * archive_filename: filename for archive to be parsed
# returns: list of filename for files contained in the archive, excluding dirs
def extract_filenames(archive_filename):
  if is_zipfile(archive_filename):
    return extract_filename_from_zip(archive_filename)
  if is_tarfile(archive_filename):
    return extract_filename_from_tar(archive_filename)
  print("Error: unknown archive file type")
  return []


# Compare file set from SPDX report with files in archive
# arguments:
#   * fds: list of FileData records produced by parseFossologySPDXReport()
#   * archive_filename: filename for archive to be parsed
# returns: dictionary with three keys:
#   * "archive_only": value is list of files only in the archive
#   * "spdx_only": value is list of files only in the SPDX report
#   * "both": value is list of files that were in both
def compare_report_to_archive(fds, archive_filename):
  arfiles = extract_filenames(archive_filename)
  comp = {}
  arfiles_set = set(arfiles)
  fds_filenames = [fd.filename for fd in fds]
  fds_set = set(fds_filenames)

  # run comparisons
  comp['archive_only'] = sorted(list(arfiles_set.difference(fds_set)))
  comp['spdx_only'] = sorted(list(fds_set.difference(arfiles_set)))
  comp['both'] = sorted(list(arfiles_set.intersection(fds_set)))
  return comp


# Create file CSV report for matching or non-matching filenames.
# arguments:
#   * comp: dictionary returned from compare_report_to_archive()
#   * key: which key to output
#   * csv_filename: filename for CSV file to be created
# returns: none
# effect:  creates three CSV files listing filesnames, one for each key
#          in the dict returned from compare_report_to_archive
def output_comparisons(comp, key, csv_filename):
  with open(csv_filename, 'w') as fout:
    # write the header line
    fout.write('"File path"\n')

    # cycle through and write each file and license
    for filename in comp[key]:
      fout.write(f'"{filename}"\n')
