# mainshell.py
#
# This is the main interactive console for the spdxSummarizer parsing and
# exporting functions.
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
import readline

from spdxSummarizer.dbtools import SPDatabase
from spdxSummarizer.parsetools import parseSPDXReport, removePrefixes
from spdxSummarizer.licenses import FTLicenseStore
from spdxSummarizer.reports import (outputCSVFull, outputExcelFull,
  outputExcelComparison)
from spdxSummarizer.spconfig import (isDBTooOld, isDBTooNew, SPVERSION,
  SPVERSION_LAST_DB_CHANGE)

prompt = '==> '

class spdxSummarizer:
  def __init__(self):
    super(spdxSummarizer, self).__init__()
    self.db = None
    self.licstore = None

  ########## HELPER FUNCTIONS ##########

  # Helper function to prompt for user input.
  # Assumes that the user has already displayed the choice text.
  # arguments:
  #   1) list of valid choices
  # returns: choice selected by user
  def shellPromptForInput(self, choices):
    # FIXME implement tab-completion in readline, esp. for filepaths
    while True:
      choice = input(prompt)
      if not choice:
        continue
      # convert to integer if we can
      try:
        choice = int(choice)
      except ValueError:
        pass

      if choice in choices:
        return choice
      else:
        print(f'Invalid choice: {choice}')
        # get all choices as strings so we can use sorted()
        # (sorted() won't work with mixed str and int types)
        str_choices = [str(i) for i in choices]
        print(f'Please choose from the following options: {sorted(str_choices)}')

  # Helper function to prompt for a scan to select.
  # Assumes that "X" will be parsed as a valid option to exit and return.
  # arguments: N/A
  # returns: scan ID if selected a scan, "X" if selected, or None otherwise
  def shellPromptToSelectScan(self):
    scans = self.db.getScansData()
    print(f'''
  Choose a scan:
    ''')
    choices = ["X", "x"]
    for (scan_id, scan_dt, desc) in scans:
      print(f'   {scan_id}) {scan_dt} - {desc}')
      choices.append(scan_id)
    print(f'   X) Return to main menu')
    print()
    return self.shellPromptForInput(choices)

  ########## DATABASE SHELL FUNCTIONS ##########

  # helper shell functions
  def _shellAskToResetDatabase(self, db_filename):
    print(f'''
  {db_filename} exists, but is not a fully-initialized spdxSummarizer database.
  Do you want to delete {db_filename}?

  1) Yes, delete it
  2) No, do not delete it
  ''')
    choice = self.shellPromptForInput([1, 2])
    if not choice == 1:
      print(f'Not deleting {db_filename}; bailing')
      return False

    print(f'Closing and deleting {db_filename}...')
    self.db.closeDatabase()
    try:
      os.remove(db_filename)
      return True

    except PermissionError as e:
      errstr = str(e)
      print(f"Error: can't delete {db_filename}: {errstr}")
      return False

  def _shellAskToCreateDatabase(self, db_filename):
    print(f'''
  {db_filename} does not exist.
  Do you want to create and initialize a new spdxSummarizer database?

  1) Yes, create and initialize a new database file
  2) No, do not create
  ''')
    choice = self.shellPromptForInput([1, 2])
    if not choice == 1:
      print(f"Not creating {db_filename}.")
      return False

    self.db = SPDatabase()
    conn = self.db.createDatabase(db_filename)
    if not conn:
      print(f"Error; failed to create {db_filename}.")
      return False

    print(f'Enter config file name [config.json]:')
    config_filename = input(prompt)
    if not config_filename:
      config_filename = "config.json"

    retval = self.db.initializeDatabaseTables(config_filename)
    if not retval:
      print(f'Error; failed to initialize {db_filename}.')
      return False

    print(f'Successfully created and initialized {db_filename}.')
    return True

  # Checks if SQLite DB file exists.  If it does, return a SPDatabase object
  # with an open connection.  If it doesn't exist, ask the user whether to
  # create and initialize it.
  # arguments:
  #   1) path to SQLite DB (passed as command line argument from main)
  # returns: SPDatabase object with opened connection if valid, or None if not
  def shellLoadDatabase(self, db_filename):
    if not db_filename:
      print("Error: must call shellLoadDatabase with path for DB file")
      return False

    # check if file exists
    if os.path.exists(db_filename):
      self.db = SPDatabase()
      retval = self.db.openDatabase(db_filename)
      if retval:
        flag_init = self.db.isInitialized()
        if flag_init:
          current_version_str = self.db.getConfigForKey("version")
          # check whether the DB needs to be migrated
          m = isDBTooOld(self.db)
          if m is None:
            print("Error; couldn't load DB version")
            return False
          elif m == True:
            print(f"Error: Database needs to be migrated (DB version is {current_version_str}; format was changed in {SPVERSION_LAST_DB_CHANGE})")
            print(f"Please run 'dbMigrate [database-path] upgrade head' from the main spdxSummarizer directory.")
            return False

          # check whether the DB is from a future version of spdxSummarizer
          m = isDBTooNew(self.db)
          if m is None:
            print("Error; couldn't load DB version")
            return False
          elif m == True:
            print(f"Error: spdxSummarizer needs to be upgraded to use this database (DB version is {current_version_str}; spdxSummarizer version is {SPVERSION})")
            print(f"Please upgrade your installation of spdxSummarizer to at least {current_version_str}.")
            return False

          # if we got here, version is good
          return True

      # if file exists but isn't initialized, offer to clear and 
      # re-create / re-initialize it
      retval = self._shellAskToResetDatabase(db_filename)
      if not retval:
        # we didn't delete the existing file, so let's exit
        return False

    # ask whether user intended to create and initialize a new DB
    return self._shellAskToCreateDatabase(db_filename)

  ########## CONFIGURATION SHELL FUNCTIONS ##########

  # View and adjust project configuration values
  # arguments: N/A
  # returns: N/A
  def shellConfigure(self):
    # first, read and print existing configuration values
    config = self.db.getConfigurableConfigData()
    if not config:
      print("Error: Couldn't load configuration data from database")
      return

    # we'll break out of loop when we return, after user chooses X
    while True:
      print(f'''
  ===================
     Configuration
  ===================''')
      config_keys = sorted(list(config.keys()))
      item = 1
      choices = ['X', 'x']
      for k in config_keys:
        v = config[k]
        print(f'  {item}) {k} => {v}')
        choices.append(item)
        item = item + 1
      print('  X) Return to main menu')
      print()
      choice = self.shellPromptForInput(choices)
      if choice == 'X' or choice == 'x':
        return

      # subtract 1 from choice b/c we count from 1, but list is zero-based
      ckey = config_keys[choice - 1]
      print(f"New value for key '{ckey}': ")
      cvalue = input(prompt)

      # update local config record and database
      config[ckey] = cvalue
      retval = self.db.setConfigValue(ckey, cvalue)
      if not retval:
        print(f"Error in shellConfigure for {ckey} => {cvalue}")
        return

  ########## SCANNING SHELL FUNCTIONS ##########

  # License and conversion import function.
  # arguments:
  #   1) list of license text names
  # returns: ldict if successfully imported any changes (or not needed),
  #   None if error
  #   ldict format: {old lic name => tuple of (new lic ID, new lic name)}
  def shellImportLicenses(self, lics):
    # ask the license store to run conversions and determine pending lics
    licenses = self.licstore.runExistingConversionsAndLicenses(lics)

    ldict = licenses.get("ldict", None)
    lpending = licenses.get("lpending", None)

    pending_total = len(lpending)
    if pending_total == 0:
      print('All licenses from scan are already mapped to known licenses.')
      return ldict

    # need to go through and parse additional licenses
    print(f'''
There are {pending_total} license strings detected that are not
currently in this spdxSummarizer database.

Do you want to review and categorize these licenses now?

1) Yes, review and categorize new license strings
2) No, cancel import and return
    ''')
    choice = self.shellPromptForInput([1, 2])
    if choice == 2:
      return None

    pending_current = 0
    for k, v in lpending.items():
      answered = False
      pending_current = pending_current + 1
      while not answered:
        print(f'''
  {pending_current} of {pending_total}: {v}

  Options:
  1) Map to existing license
  2) Map to new license
  X) Cancel import and return
        ''')
        choice = self.shellPromptForInput([1, 2, "X", "x"])
        if choice == "X" or choice == "x":
          return None

        elif choice == 1:
          # show and select from existing licenses
          print('''
-----
| Existing licenses:''')
          lic_ids = [0]
          for lic_id, ftlic in self.licstore.licenses.items():
            print(f'  | {lic_id}) {ftlic.short_name}')
            lic_ids.append(lic_id)
          print('  | 0) None of these; go back')
          print()
          print(f'Select an existing license to map {v}:')
          choice = self.shellPromptForInput(lic_ids)
          if choice == 0:
            # didn't answer; go back to loop for this license string
            continue
          else:
            # create a new conversion for this license string
            self.licstore.createConversionInStore(v, choice)
            # and go ahead and update this entry in ldict
            lic_text = self.licstore.licenses[choice].short_name
            ldict[k] = (choice, lic_text)
            # and we're done with this one
            print()
            print(f"*** Mapped {v} to {choice}: {lic_text}")
            answered = True

        else:
          # create a new license entry
          print(f'Enter name for new license or "exit" to go back [{v}]:')
          new_lic_name = input(prompt)
          if new_lic_name == "exit":
            # go back to loop for this license string
            continue
          if not new_lic_name:
            new_lic_name = v

          # if we're here, want to create a new license string, new_lic_name
          # ask which category it should have
          print(f'''
-----
| Choose a category for {new_lic_name}:
| ''')
          cat_ids = [0, "X", "x"]
          for cat_id, ftcat in self.licstore.categories.items():
            print(f'  | {cat_id}) {ftcat.name}')
            cat_ids.append(cat_id)
          print('  | 0) Create a new category')
          print('  | X) None of these; go back')
          print()
          print(f'Select a category for {new_lic_name}:')
          choice = self.shellPromptForInput(cat_ids)
          if choice == "X" or choice == "x":
            # didn't answer; go back to loop for this license string
            continue
          elif choice == 0:
            print('Enter name for new category:')
            new_cat_name = input(prompt)
            # create a new conversion for this license string
            new_lic_category_id = self.licstore.createCategoryInStore(new_cat_name)
            if not new_lic_category_id:
              print(f"Error: couldn't create new category {new_cat_name}")
              return None
          else:
            # selected an existing category
            new_lic_category_id = choice

          # okay.  now we have the right category ID, and the new
          # license name.  time to create it.
          new_lic_id = self.licstore.createLicenseInStore(
            new_lic_name, new_lic_category_id)
          if not new_lic_id:
            print(f"Error: couldn't create new license {new_lic_name}")
            return None

          # finally, update the license mapping in ldict
          ldict[k] = (new_lic_id, new_lic_name)
          # and we're done with this one
          print()
          print(f"*** Mapped {v} to {new_lic_id}: {new_lic_name}")
          answered = True

    print("All licenses are now mapped.")
    print("Saving out any new categories, licenses and conversions to database...")
    retval = self.licstore.saveAllModifiedToDatabase()
    if not retval:
      print("Error in saving new items to database; exiting import")
      return None
    else:
      self.db.commitChanges()
      print("Finished with saving out new items and remapping.")
      return ldict

  # Main scan import function
  # arguments:
  #   1) path to SPDX tag:value file
  # returns: True if processed a scan, False otherwise
  def shellImportScan(self, report_filename):
    # first, reload the existing license store
    self.licstore = FTLicenseStore(self.db)
    self.licstore.loadLicensesFromDB()
    self.licstore.loadConversionsFromDB()
    self.licstore.loadCategoriesFromDB()

    # try loading the SPDX report from this path
    fds = parseSPDXReport(report_filename)
    if fds == None or fds == []:
      print(f"Got invalid result when trying to parse SPDX report from {report_filename}")
      return False

    # if we get here, then we were able to parse the report
    print()
    print(f"Successfully parsed report; found {len(fds)} file records.")

    # now do the following (some in parsetools):

    # clean up results (e.g., strip out prefixes)
    prefix = removePrefixes(fds)
    print(f"Removed prefix {prefix}")
    print()

    # go to subfunction to apply conversions, parse license strings
    # and add new ones
    lics = [fd.license for fd in fds]
    ldict = self.shellImportLicenses(lics)
    if not ldict:
      print(f"Error when importing and converting license strings.")
      return False

    # we're ready to go ahead and confirm about importing the scan
    print('''
  Are you ready to import the scan results into the spdxSummarizer database?

  1) Yes, import the scan results
  2) No, return to main menu
    ''')
    choice = self.shellPromptForInput([1, 2])
    if choice == 2:
      print('Not importing results; exiting scan import.')
      return False

    # get additional data regarding scan
    print('Enter date of scan (in format YYYY-MM-DD):')
    scan_dt = input(prompt)
    print('Enter brief description of scan:')
    desc = input(prompt)

    print()
    print("Beginning save to database...")
    print()

    # add scan to database; tell it not to commit yet
    scan_id = self.db.addNewScan(scan_dt, desc, False)
    if scan_id == -1:
      print("Error: couldn't create new scan record in database.")
      return False
    print(f"Created new scan with database ID {scan_id}.")

    # now, cycle through and add files
    file_tuples = []
    for fd in fds:
      # look up the license ID from ldict, NOT from licstore
      lt = ldict.get(fd.license, None)
      if lt == None:
        print(f"Error: couldn't get matched license for {fd.filename}; rolling back and canceling import.")
        self.db.rollbackChanges()
        return False
      # now we've got the right license ID, so add to list of file tuples
      # which we'll submit in bulk below
      file_tuple = (fd.filename, lt[0], fd.md5, fd.sha1)
      file_tuples.append(file_tuple)

    # submit list of file tuples in bulk to add to database
    retval = self.db.addBulkNewFiles(scan_id, file_tuples, True)
    if not retval:
      print(f"Error: couldn't add files for scan {scan_id} to database; rolling back and canceling import.")
      self.db.rollbackChanges()
      return False

    # and we're done!
    print(f"Saved {len(file_tuples)} files to database for scan {scan_id}.")
    return True

  # Initial scan request.  Ask the user to tell us where to find the SPDX
  # tag:value file for the initial scan.
  # arguments: N/A
  # returns: True if processed a scan, False otherwise
  def shellInitialScanRequest(self):
    print(f'''
  The spdxSummarizer database contains no scans.
  
  Please enter the path to an SPDX tag:value report to import.
  Or, type "exit" to quit.
    ''')
    path = input(prompt)
    if path == "exit":
      return False

    retval = self.shellImportScan(path)
    if retval == False:
      print(f"Couldn't import initial scan report from {path}; exiting")
      return False

    return True

  # New scan request.  Ask the user to tell us where to find the SPDX
  # tag:value file for a subsequent scan.
  # arguments: N/A
  # returns: True if processed a scan, False otherwise
  def shellNewScanRequest(self):
    print(f'''
  Please enter the path to a new SPDX tag:value report to import.
  Or, type "exit" to cancel.
    ''')
    path = input(prompt)
    if path == "exit":
      return False

    retval = self.shellImportScan(path)
    if retval == False:
      print(f"Couldn't import scan report from {path}.")
      return False

    return True


  ########## REPORT GENERATION SHELL FUNCTIONS ##########

  # Prompts for CSV report generator - path and license for all files
  # in a scan.
  # arguments: N/A
  # returns: True if generated a report, False otherwise
  def shellGenerateCSVFull(self):
    choice = self.shellPromptToSelectScan()
    if choice == "X" or choice == "x":
      return False

    # get output CSV filename
    print("Enter filename for CSV file to be generated:")
    csv_filename = input(prompt)
    return outputCSVFull(self.db, choice, csv_filename)


  # Prompts for Excel full report generator - path and license for all files
  # in a scan.
  # arguments: N/A
  # returns: True if generated a report, False otherwise
  def shellGenerateExcelFull(self):
    choice = self.shellPromptToSelectScan()
    if choice == "X" or choice == "x":
      return False

    # get output XLSX filename
    print("Enter filename for XLSX full file to be generated:")
    xlsx_filename = input(prompt)
    return outputExcelFull(self.db, choice, xlsx_filename)


  # Prompts for Excel report generator - compare two scans
  # arguments: N/A
  # returns: True if generated a report, False otherwise
  def shellGenerateExcelComparison(self):
    selecting = True
    while selecting:
      print()
      print("Select first scan for comparison:")
      first_scan_id = self.shellPromptToSelectScan()
      if first_scan_id == "X" or first_scan_id == "x":
        return False

      print()
      print("Select second scan for comparison:")
      second_scan_id = self.shellPromptToSelectScan()
      if second_scan_id == "X" or second_scan_id == "x":
        return False

      if first_scan_id == second_scan_id:
        print()
        print("Must select two different scans!")
        print("Press enter to continue...")
        input(prompt)
      else:
        selecting = False

    # get output XLSX filename
    print()
    print("Enter filename for XLSX comparison file to be generated:")
    xlsx_filename = input(prompt)
    return outputExcelComparison(self.db, first_scan_id, second_scan_id,
      xlsx_filename)


  ########## MAIN SHELL FUNCTION ##########

  # Main shell loop.  The high-level program flow is just a REPL cycle
  # through this function.
  # arguments:
  #   1) path to SQLite DB (passed as command line argument from main)
  # returns: N/A
  def shellMainLoop(self, db_filename):
    # try to load the database, or to create it if needed
    retval = self.shellLoadDatabase(db_filename)
    if not retval:
      return

    # at intro, check whether there are any existing scans
    scan_ids = self.db.getScansIDList()
    if not scan_ids:
      # there are no existing scans; go ask the user to import one
      retval = self.shellInitialScanRequest()
      if not retval:
        return

    # main loop
    running = True
    while running:
      scan_ids = self.db.getScansIDList()
      if (len(scan_ids) == 1):
        scan_str = "There is 1 scan"
      else:
        scan_str = f"There are {len(scan_ids)} scans"

      print(f'''
===================
     MAIN MENU
===================
spdxSummarizer database: {db_filename}
{scan_str} currently in the database.

  CONFIGURE:
    1) Configure project database

  IMPORT:
    2) Import a new SPDX scan report

  REPORT:
    3) Generate Excel full report
    4) Generate Excel report comparing two scans
    5) Generate CSV file listing

    X) Exit
    ''')
      choice = self.shellPromptForInput([1, 2, 3, 4, 5, "X", "x"])
      if choice == 1:
        retval = self.shellConfigure()
        print()

      elif choice == 2:
        retval = self.shellNewScanRequest()
        print()
        if retval:
          print('Imported scan.')
        else:
          print("Didn't import scan.")
        print()

      elif choice == 3:
        retval = self.shellGenerateExcelFull()
        print()
        if retval:
          print('Generated Excel file listing.')
        else:
          print("Didn't generate Excel file listing.")
        print()

      elif choice == 4:
        retval = self.shellGenerateExcelComparison()
        print()
        if retval:
          print('Generated Excel comparison listing.')
        else:
          print("Didn't generate Excel comparison listing.")
        print()

      elif choice == 5:
        retval = self.shellGenerateCSVFull()
        print()
        if retval:
          print('Generated CSV file listing.')
        else:
          print("Didn't generate CSV file listing.")
        print()

      elif choice == "X" or choice == "x":
        running = False

    # exiting
    self.db.closeDatabase()
    

########## initial entry point ##########

if __name__ == "__main__":
  if len(sys.argv) == 2:
    toolkit = spdxSummarizer()
    db_filename = sys.argv[1]
    toolkit.shellMainLoop(db_filename)
    print("Exiting.")
  else:
    print(f"Usage: {sys.argv[0]} dbfile")
