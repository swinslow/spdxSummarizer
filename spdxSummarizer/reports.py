# reports.py
#
# This module contains functions for generating spdxSummarizer reports in 
# various formats.
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

from operator import itemgetter
from xlsxwriter.workbook import Workbook

from spdxSummarizer.analysis import (analyzeFileExtensions,
  analyzeFileExtensionsForFlatDict, analyzeVendorFiles,
  analyzeVendorFilesForFlatDict)

# Create a file/license CSV report.
# arguments:
#   1) db: SPDatabase
#   2) scan_id: ID of scan
#   3) csv_filename: filename for CSV output file to be created
# returns: True if successfully created CSV file, False otherwise
def outputCSVFull(db, scan_id, csv_filename):
  # get dict of filename => license for this scan; exclude /.git/ files
  records = db.getLicenseAndFilesForScan(scan_id, True)
  if not records:
    print(f"Couldn't get scan results for scan {scan_id}")
    return False

  # analyze and split out files with no license found
  retval = analyzeFileExtensionsForFlatDict(db, records)
  if not retval:
    print(f"Error when trying to analyze for ignored file extensions.")
    # don't exit, keep going as-is
  retval = analyzeVendorFilesForFlatDict(db, records)
  if not retval:
    print(f"Error when trying to analyze for vendor files.")
    # don't exit, keep going as-is

  try:
    # get sorted list of filenames
    filenames = sorted(list(records.keys()))

    with open(csv_filename, 'w') as fout:
      # write the header line
      fout.write('"File path", License\n')

      # cycle through and write each file and license
      for filename in filenames:
        license = records[filename]
        fout.write(f'"{filename}","{license}"\n')

    return True

  except Exception as e:
    print(f"Couldn't output CSV full listing to {csv_filename}: {str(e)}")
    return False


# Create a full Excel report.
# arguments:
#   1) db: SPDatabase
#   2) scan_id: ID of scan
#   3) xlsx_filename: filename for XLSX output file to be created
# returns: True if successfully created report, False otherwise
def outputExcelFull(db, scan_id, xlsx_filename):
  # get categories and files; exclude /.git/ files
  cats = db.getCategoryFilesForScan(scan_id, True)

  # cats has: dict of category => 
  #    (category_name, {filename => license}, {license => count})
  #   or None if error
  if not cats:
    print(f"Couldn't get category/file scan results from database for scan {scan_id}.")
    return False

  # analyze and split out files with no license found
  retval = analyzeFileExtensions(db, cats)
  if not retval:
    print(f"Error when trying to analyze for ignored file extensions.")
    # don't exit, keep going as-is
  retval = analyzeVendorFiles(db, cats)
  if not retval:
    print(f"Error when trying to analyze for vendor files.")
    # don't exit, keep going as-is

  try:
    with Workbook(xlsx_filename) as workbook:
      # prepare formats
      bold = workbook.add_format({'bold': True})
      bold.set_font_size(16)
      normal = workbook.add_format()
      normal.set_font_size(14)

      ##### STATS PAGE #####

      # build stats page
      statsSheet = workbook.add_worksheet("License counts")
      statsSheet.write(0, 0, "License", bold)
      statsSheet.write(0, 2, "# of files", bold)
      # set column widths
      statsSheet.set_column(0, 0, 2)
      statsSheet.set_column(1, 1, 58)
      statsSheet.set_column(2, 2, 10)

      total = 0
      row = 2
      for cat_id, cat_data in cats.items():
        cat_name = cat_data[0]
        cat_stats = cat_data[2]

        # print category name in bold in column A
        statsSheet.write(row, 0, cat_name + ":", bold)
        row = row + 1

        # now, loop through licenses in this category,
        # outputting name in col B and count in col C
        for lic_name, lic_count in cat_stats.items():
          statsSheet.write(row, 1, lic_name, normal)
          statsSheet.write(row, 2, lic_count, normal)
          total = total + lic_count
          row = row + 1

      # at the end, skip another row, then output the total
      row = row + 1
      statsSheet.write(row, 0, "TOTAL", bold)
      statsSheet.write(row, 2, total, bold)

      ##### CATEGORY PAGES #####

      for cat_id, cat_data in cats.items():
        cat_name = cat_data[0]
        cat_files = cat_data[1]

        # build filename / license page for each category
        fileSheet = workbook.add_worksheet(cat_name)
        fileSheet.write(0, 0, "File", bold)
        fileSheet.write(0, 1, "License", bold)
        # set column widths
        fileSheet.set_column(0, 0, 100)
        fileSheet.set_column(1, 1, 60)

        # create list of tuples: (filename, license) so we can sort it
        filetuples = []
        for filename, license in cat_files.items():
          ft = (filename, license)
          filetuples.append(ft)
        # now, sort by license and then by filename
        filetuples = sorted(filetuples, key=itemgetter(1, 0))

        # now, loop through files and licenses in this category,
        # outputting filename in col A and license in col B
        row = 1
        for filename, license in filetuples:
          fileSheet.write(row, 0, filename, normal)
          fileSheet.write(row, 1, license, normal)
          row = row + 1

    # ... and that's it!
    return True

  except Exception as e:
    print(f"Couldn't output Excel full listing to {xlsx_filename}: {str(e)}")
    return False


# Analyze two scans and generate report of:
#   * files in both where license has changed
#   * files just in old
#   * files just in new
# arguments:
#   1) db: SPDatabase
#   2) first_scan_id:  ID of first scan
#   3) second_scan_id: ID of second scan
#   4) xlsx_filename: filename for XLSX output file to be created
# returns: True if successfully created report, False otherwise
def outputExcelComparison(db, first_scan_id, second_scan_id, xlsx_filename):
  # get dicts of filename => license for each scan; exclude /.git/ files
  first_files = db.getLicenseAndFilesForScan(first_scan_id, True)
  if not first_files:
    print(f"Couldn't get scan results for scan {first_scan_id}")
    return False
  second_files = db.getLicenseAndFilesForScan(second_scan_id, True)
  if not second_files:
    print(f"Couldn't get scan results for scan {second_scan_id}")
    return False

  # pull out just the filenames
  first_filenames = set(first_files.keys())
  second_filenames = set(second_files.keys())

  # compare sets and convert to sorted lists:
  in_first_only = sorted(list(first_filenames.difference(second_filenames)))
  in_second_only = sorted(list(second_filenames.difference(first_filenames)))
  in_both = sorted(list(first_filenames.intersection(second_filenames)))

  # now, get those in both where license has changed
  # create list of tuples (filename, first_lic, second_lic) where changed
  changed_lics = []
  for filename in in_both:
    first_license = first_files[filename]
    second_license = second_files[filename]
    if first_license != second_license:
      t = (filename, first_license, second_license)
      changed_lics.append(t)

  # now, start generating the report
  try:
    with Workbook(xlsx_filename) as workbook:
      # prepare formats
      bold = workbook.add_format({'bold': True})
      bold.set_font_size(16)
      normal = workbook.add_format()
      normal.set_font_size(14)

      ##### CHANGED LICENSES PAGE #####

      # build changed licenses page
      changedSheet = workbook.add_worksheet("Changed licenses")
      changedSheet.write(0, 0, "File", bold)
      changedSheet.write(0, 1, "First License", bold)
      changedSheet.write(0, 2, "Second License", bold)
      # set column widths
      changedSheet.set_column(0, 0, 100)
      changedSheet.set_column(1, 1, 60)
      changedSheet.set_column(2, 2, 60)

      # now, loop through files where license has changed,
      # outputting filename in col A and license in col B
      row = 1
      for t in changed_lics:
        filename = t[0]
        first_license = t[1]
        second_license = t[2]
        changedSheet.write(row, 0, filename, normal)
        changedSheet.write(row, 1, first_license, normal)
        changedSheet.write(row, 2, second_license, normal)
        row = row + 1

      ##### FIRST-ONLY FILES PAGE #####

      # build first-only files and licenses page
      firstonlySheet = workbook.add_worksheet("In first only")
      firstonlySheet.write(0, 0, "File", bold)
      firstonlySheet.write(0, 1, "License", bold)
      # set column widths
      firstonlySheet.set_column(0, 0, 100)
      firstonlySheet.set_column(1, 1, 60)

      # now, loop through files and licenses in this list,
      # outputting filename in col A and license in col B
      row = 1
      for filename in in_first_only:
        license = first_files[filename]
        firstonlySheet.write(row, 0, filename, normal)
        firstonlySheet.write(row, 1, license, normal)
        row = row + 1

      ##### SECOND-ONLY FILES PAGE #####

      # build second-only files and licenses page
      secondonlySheet = workbook.add_worksheet("In second only")
      secondonlySheet.write(0, 0, "File", bold)
      secondonlySheet.write(0, 1, "License", bold)
      # set column widths
      secondonlySheet.set_column(0, 0, 100)
      secondonlySheet.set_column(1, 1, 60)

      # now, loop through files and licenses in this list,
      # outputting filename in col A and license in col B
      row = 1
      for filename in in_second_only:
        license = second_files[filename]
        secondonlySheet.write(row, 0, filename, normal)
        secondonlySheet.write(row, 1, license, normal)
        row = row + 1

    # ... and that's it!
    return True

  except Exception as e:
    print(f"Couldn't output Excel comparison listing to {xlsx_filename}: {str(e)}")
    return False