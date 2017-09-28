# dbtools.py
#
# This module contains the FTDatabase class, for interacting with a SQLite
# database which stores scan results and license data in spdxSummarizer.
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

import sqlite3
import json
import os

from spdxSummarizer.ftconfig import FTVERSION

class FTDatabase(object):
  def __init__(self):
    super(FTDatabase, self).__init__()
    self.conn = None
    self.c = None
    self.internal_configs = ["magic", "initialized", "version"]


  def closeDatabase(self):
    if self.conn:
      self.c = None
      self.conn.close()
      self.conn = None


  # create new uninitialized spdxSummarizer database
  # WARNING: will delete the specified DB file if it already exists
  # arguments:
  #   1) db_filename: string with path to database file
  # returns: connection to database on success, None on failure
  def createDatabase(self, db_filename):
    if db_filename != ":memory:":
      # delete file if it already exists
      if os.path.exists(db_filename):
        try:
          os.remove(db_filename)
        except PermissionError as e:
          errstr = str(e)
          print(f"{db_filename} exists and can't be deleted: {errstr}")
          return None

    # create and connect to database
    self.conn = sqlite3.connect(db_filename)
    self.c = self.conn.cursor()

    # create tables
    self.c.execute('''
      CREATE TABLE config (
        key TEXT UNIQUE,
        value TEXT
      )''')
    # insert basic beginner config values
    self.c.execute('INSERT INTO config VALUES (?, ?)', 
      ["magic", "spdxSummarizer"])
    self.c.execute('INSERT INTO config VALUES (?, ?)', 
      ["initialized", "no"])

    self.c.execute('''
      CREATE TABLE scans (
        id INTEGER PRIMARY KEY NOT NULL,
        scan_dt TEXT,
        desc TEXT
      )''')

    self.c.execute('''
      CREATE TABLE categories (
        id INTEGER PRIMARY KEY NOT NULL,
        name TEXT
      )''')

    self.c.execute('''
      CREATE TABLE licenses (
        id INTEGER PRIMARY KEY NOT NULL,
        short_name TEXT,
        category_id INTEGER,
        FOREIGN KEY (category_id) REFERENCES categories (id)
        ON DELETE SET NULL ON UPDATE NO ACTION
      )''')

    self.c.execute('''
      CREATE TABLE files (
        id INTEGER PRIMARY KEY NOT NULL,
        scan_id INTEGER,
        filename TEXT,
        license_id INTEGER,
        md5 TEXT,
        sha1 TEXT,
        FOREIGN KEY (scan_id) REFERENCES scans (id)
        ON DELETE CASCADE ON UPDATE NO ACTION,
        FOREIGN KEY (license_id) REFERENCES licenses (id)
        ON DELETE SET NULL ON UPDATE NO ACTION
      )''')

    self.c.execute('''
      CREATE TABLE conversions (
        id INTEGER PRIMARY KEY NOT NULL,
        old_text TEXT,
        new_license_id INTEGER,
        FOREIGN KEY (new_license_id) REFERENCES licenses (id)
        ON DELETE SET NULL ON UPDATE NO ACTION
      )''')

    self.conn.commit()
    return self.conn


  # get connection to existing spdxSummarizer database, and confirm
  # that it is a valid spdxSummarizer database
  # arguments:
  #   1) db_filename: string with path to database file
  # returns: connection to database on success, None on failure
  def getDatabaseConn(self, db_filename):
    if os.path.exists(db_filename):
      self.conn = sqlite3.connect(db_filename)
      if not self.conn:
        print(f"Couldn't open SQLite database at {db_filename}.")
        return None

      # verify we can get the magic number
      self.c = self.conn.cursor()
      try:
        self.c.execute('SELECT value FROM config WHERE key = "magic"')
        retval = self.c.fetchone()
        if retval != None and retval[0] == "spdxSummarizer":
          # we're good; return the connection object
          return self.conn
      except Exception as e:
        print(f'Error checking magic number: {str(e)}')

      print(f"Couldn't load magic number from {db_filename}.")
      return None

    else:
      print(f"No file found at {db_filename}.")
      return None

  # Commit changes to database.  Typically called when calling something
  # like addNewScan() and addNewFile() repeatedly, but when wanting to
  # finish all before committing.
  # arguments: N/A
  # returns: N/A
  def commitChanges(self):
    if self.conn:
      self.conn.commit()


  # Roll back changes to database since last commit.  Typically called when
  # encountering an error during e.g. a set of calls to addNewFile().
  # arguments: N/A
  # returns: N/A
  def rollbackChanges(self):
    if self.conn:
      self.conn.rollback()


  # Initialize config table based on dict already read from JSON file.
  # arguments:
  #   1) config_dict: dictionary with key/value config strings
  # returns: True if successful, False on error
  def initializeConfigTable(self, config_dict):
    for (key, value) in config_dict.items():
      self.c.execute('INSERT INTO config (key, value) VALUES (?, ?)', 
        [key, value])
    return True


  # Initialize categories and licenses tables based on dict already read 
  # from JSON file.
  # arguments:
  #   1) categories_list: list of categories objects
  # returns: True if successful, False on error
  def initializeCategoriesAndLicensesTable(self, categories_list):
    # walk through and parse each category object in the list
    for category in categories_list:
      cid = category.get('id', None)
      cname = category.get('name', None)
      licenses = category.get('licenses', None)
      if cid == None or cname == None or licenses == None:
        print(f'Invalid parameter in JSON config: category id {cid}, name {cname}, licenses {licenses}')
        return False

      # add to categories table
      self.c.execute('INSERT INTO categories (id, name) VALUES (?, ?)', 
        [cid, cname])

      # now, walk through licenses list and add each to licenses table
      # note that we might legitimately not have any licenses for 
      # a given category
      for license in licenses:
        self.c.execute(
          'INSERT INTO licenses (short_name, category_id) VALUES (?, ?)',
          [license, cid]
        )

    return True


  # Initialize conversions tables based on dict already read from JSON file.
  # arguments:
  #   1) conversions_dict: dict of conversion objects
  # returns: True if successful, False on error
  def initializeConversionsTable(self, conversions_dict):
    # walk through and parse each conversion key/value pair
    for (old_text, new_license) in conversions_dict.items():
      # look up ID for new license text
      self.c.execute('SELECT id FROM licenses WHERE short_name = ?',
        [new_license])
      retval = self.c.fetchone()
      if retval != None:
        new_license_id = retval[0]
        self.c.execute('INSERT INTO conversions (old_text, new_license_id) VALUES (?, ?)',
          [old_text, new_license_id])
      else:
        print(f"Couldn't find license ID in database for {old_text}: {new_license}")
        return False

    return True


  # Initialize config, categories, licenses and conversions tables based 
  # on config JSON file.
  # arguments:
  #   1) json_filename: string with path to JSON config file
  # returns: True if successful, False on error
  def initializeDatabaseTables(self, json_filename):
    try:
      with open(json_filename, 'r') as f:
        js = json.load(f)

        # pull out the expected top-level parameters
        config = js.get('config', {})
        categories = js.get('categories', [])
        conversions = js.get('conversions', {})
        
        # make sure we at least got a valid config dict + project string
        project = config.get("project", None)
        if not project:
          print(f'Unable to load valid JSON config file at {json_filename}')
          return False

        # initialize tables
        retval = self.initializeConfigTable(config)
        if (retval == False): 
          return False

        retval = self.initializeCategoriesAndLicensesTable(categories)
        if (retval == False): 
          return False

        # note that categories and licenses tables need to be
        # initialized before conversions table, since conversions 
        # has a foreign key reference to the licenses table
        retval = self.initializeConversionsTable(conversions)
        if (retval == False): 
          return False

        # if we got here, go ahead and mark config as initialized
        self.c.execute("UPDATE config SET value = ? WHERE key = ?",
          ["yes", "initialized"])
        self.c.execute("INSERT INTO config (key, value) VALUES (?, ?)",
          ["version", FTVERSION])

        self.conn.commit()
        return True

    except json.decoder.JSONDecodeError as e:
      print(f'Error loading or parsing {json_filename}: {str(e)}')
      return False

  ########## CONFIG DATA FUNCTIONS ##########

  # Return boolean for whether the DB was fully initialized.
  # arguments: N/A
  # returns: True if "initialized" in config is "yes", False otherwise
  def isInitialized(self):
    if not self.conn or not self.c:
      return False

    self.c.execute('SELECT value FROM config WHERE key = "initialized"')
    res = self.c.fetchone()
    if res != None and res[0] == "yes":
      return True
    return False

  ########## SCAN DATA FUNCTIONS ##########

  # Get a list of IDs for all prior scans.
  # arguments: N/A
  # returns: list of IDs from all scans in database
  def getScansIDList(self):
    self.c.execute("SELECT id FROM scans ORDER BY id")
    res = self.c.fetchall()
    idlist = [t[0] for t in res]
    return idlist

  # Get all data for all prior scans.
  # arguments: N/A
  # returns: list of data tuples from all scans in database
  #   tuple format: (id, scan_dt, desc)
  def getScansData(self):
    self.c.execute("SELECT id, scan_dt, desc FROM scans ORDER BY id")
    return self.c.fetchall()

  # Get all data for prior scan with given ID.
  # arguments:
  #   1) ID of prior scan
  # returns: tuple of data if found or None if not found
  #   tuple format: (id, scan_dt, desc)
  def getScanData(self, scan_id):
    self.c.execute("SELECT id, scan_dt, desc FROM scans WHERE id = ? ORDER BY id", [scan_id])
    return self.c.fetchone()

  # Add new scan to database.
  # arguments:
  #   1) scan date
  #   2) description (optional)
  #   3) commit: if True, commit updates at end
  # returns: new ID for scan if successfully added to DB, or -1 otherwise
  def addNewScan(self, scan_dt, desc="no description", commit=True):
    if not self.isInitialized():
      print(f"Cannot add new scan; DB is not initialized")
      return -1

    try:
      self.c.execute("INSERT INTO scans (scan_dt, desc) VALUES (?, ?)",
        [scan_dt, desc])
      self.c.execute("SELECT last_insert_rowid()")
      res = self.c.fetchone()
      if commit:
        self.conn.commit()
      return res[0]
    except Exception as e:
      print(f'Error adding new scan {desc}: {str(e)}')
      return -1

  ########## CATEGORY DATA FUNCTIONS ##########

  # Get a list of IDs for all known categories.
  # arguments: N/A
  # returns: list of IDs from all categories in database
  def getCategoriesIDList(self):
    self.c.execute("SELECT id FROM categories ORDER BY id")
    res = self.c.fetchall()
    idlist = [t[0] for t in res]
    return idlist

  # Get all data for all known categories.
  # arguments: N/A
  # returns: list of data tuples from all categories in database
  #   tuple format: (id, name)
  def getCategoriesData(self):
    self.c.execute("SELECT id, name FROM categories ORDER BY id")
    return self.c.fetchall()

  # Get all data for known category with given ID.
  # arguments:
  #   1) ID of category
  # returns: tuple of data if found or None if not found
  #   tuple format: (id, name)
  def getCategoryData(self, category_id):
    self.c.execute("SELECT id, name FROM categories WHERE id = ? ORDER BY id", [category_id])
    return self.c.fetchone()

  # Add new category to database.
  # arguments:
  #   1) name for category
  #   2) commit: if True, commit updates at end
  #   3) id: if non-zero, use this for new ID
  # returns: new ID for category if successfully added to DB, or -1 otherwise
  def addNewCategory(self, name, commit=True, id=0):
    try:
      if id == 0:
        self.c.execute("INSERT INTO categories (name) VALUES (?)",
          [name])
      else:
        self.c.execute("INSERT INTO categories (name, id) VALUES (?, ?)",
        [name, id])
      self.c.execute("SELECT last_insert_rowid()")
      res = self.c.fetchone()
      if commit:
        self.conn.commit()
      return res[0]
    except Exception as e:
      print(f'Error adding new category {name}: {str(e)}')
      return -1

  ########## LICENSE DATA FUNCTIONS ##########

  # Get a list of IDs for all known licenses.
  # arguments: N/A
  # returns: list of IDs from all licenses in database
  def getLicensesIDList(self):
    self.c.execute("SELECT id FROM licenses ORDER BY id")
    res = self.c.fetchall()
    idlist = [t[0] for t in res]
    return idlist

  # Get all data for all known licenses.
  # arguments: N/A
  # returns: list of data tuples from all licenses in database
  #   tuple format: (id, short_name, category_id)
  def getLicensesData(self):
    self.c.execute("SELECT id, short_name, category_id FROM licenses ORDER BY id")
    return self.c.fetchall()

  # Get all data for known license with given ID.
  # arguments:
  #   1) ID of license
  # returns: tuple of data if found or None if not found
  #   tuple format: (id, short_name, category_id)
  def getLicenseData(self, license_id):
    self.c.execute("SELECT id, short_name, category_id FROM licenses WHERE id = ? ORDER BY id", [license_id])
    return self.c.fetchone()

  # Add new license to database.
  # arguments:
  #   1) short name for license
  #   2) category ID
  #   3) commit: if True, commit updates at end
  #   4) id: if non-zero, use this for new ID
  # returns: new ID for license if successfully added to DB, or -1 otherwise
  def addNewLicense(self, short_name, category_id, commit=True, id=0):
    try:
      if id == 0:
        self.c.execute("INSERT INTO licenses (short_name, category_id) VALUES (?, ?)",
          [short_name, category_id])
      else:
        self.c.execute("INSERT INTO licenses (short_name, category_id, id) VALUES (?, ?, ?)",
          [short_name, category_id, id])
      self.c.execute("SELECT last_insert_rowid()")
      res = self.c.fetchone()
      if commit:
        self.conn.commit()
      return res[0]
    except Exception as e:
      print(f'Error adding new license {short_name}: {str(e)}')
      return -1

  ########## CONVERSION DATA FUNCTIONS ##########

  # Get a list of IDs for all known conversions.
  # arguments: N/A
  # returns: list of IDs from all conversions in database
  def getConversionsIDList(self):
    self.c.execute("SELECT id FROM conversions ORDER BY id")
    res = self.c.fetchall()
    idlist = [t[0] for t in res]
    return idlist

  # Get all data for all known conversions.
  # arguments: N/A
  # returns: list of data tuples from all conversions in database
  #   tuple format: (id, old_text, new_license_id)
  def getConversionsData(self):
    self.c.execute("SELECT id, old_text, new_license_id FROM conversions ORDER BY id")
    return self.c.fetchall()

  # Get all data for known conversions with given ID.
  # arguments:
  #   1) ID of conversions
  # returns: tuple of data if found or None if not found
  #   tuple format: (id, old_text, new_license_id)
  def getConversionData(self, conversion_id):
    self.c.execute("SELECT id, old_text, new_license_id FROM conversions WHERE id = ? ORDER BY id", [conversion_id])
    return self.c.fetchone()

  # Add new conversion to database.
  # arguments:
  #   1) old license text
  #   2) ID of new license being converted to
  #   3) commit: if True, commit updates at end
  #   4) id: if non-zero, use this for new ID
  # returns: new ID for conversion if successfully added to DB, or -1 otherwise
  def addNewConversion(self, old_text, new_license_id, commit=True, id=0):
    try:
      if id == 0:
        self.c.execute("INSERT INTO conversions (old_text, new_license_id) VALUES (?, ?)",
          [old_text, new_license_id])
      else:
        self.c.execute("INSERT INTO conversions (old_text, new_license_id, id) VALUES (?, ?, ?)",
          [old_text, new_license_id, id])
      self.c.execute("SELECT last_insert_rowid()")
      res = self.c.fetchone()
      if commit:
        self.conn.commit()
      return res[0]
    except Exception as e:
      print(f'Error adding new conversion {old_text} => {new_license_id}: {str(e)}')
      return -1

  ########## FILE DATA FUNCTIONS ##########

  # Get all data for file with given ID.
  # arguments:
  #   1) ID of file
  # returns: tuple of data if found or None if not found
  #   tuple format: (id, scan_id, filename, license_id, md5, sha1)
  def getFileData(self, file_id):
    self.c.execute("SELECT id, scan_id, filename, license_id, md5, sha1 FROM files WHERE id = ? ORDER BY id", [file_id])
    return self.c.fetchone()

  # Get all data for file with given scan ID and filename.
  # arguments:
  #   1) ID of scan
  #   2) filename
  # returns: tuple of data if found or None if not found
  #   tuple format: (id, scan_id, filename, license_id, md5, sha1)
  def getFileInstanceData(self, scan_id, filename):
    self.c.execute("SELECT id, scan_id, filename, license_id, md5, sha1 FROM files WHERE scan_id = ? and filename = ? ORDER BY id", [scan_id, filename])
    return self.c.fetchone()

  # Add new file to database.
  # arguments:
  #   1) ID of scan
  #   2) filename
  #   3) ID of license
  #   4) MD5 string
  #   5) SHA1 string
  #   6) commit: if True, commit updates at end
  # returns: new ID for file if successfully added to DB, or -1 otherwise
  # NOTE that scan and license IDs are foreign key constraints, so those must
  #      be added prior to adding a file that references them
  def addNewFile(self, scan_id, filename, license_id, md5, sha1, commit=True):
    try:
      self.c.execute("INSERT INTO files (scan_id, filename, license_id, md5, sha1) VALUES (?, ?, ?, ?, ?)",
        [scan_id, filename, license_id, md5, sha1])
      self.c.execute("SELECT last_insert_rowid()")
      res = self.c.fetchone()
      if commit:
        self.conn.commit()
      return res[0]
    except Exception as e:
      print(f'Error adding new file {filename}: {str(e)}')
      return -1

  ########## COMBO DATA FUNCTIONS ##########

  # Get file and license info, by category, for all files for a given scan.
  # arguments:
  #   1) ID of scan
  #   2) (optional) if True, exclude files in any /.git/ subdirectory
  # returns: dict of category =>
  #    (category_name, {filename => license}, {license => count})
  #   or None if error
  def getCategoryFilesForScan(self, scan_id, exclude_git=False):
    if exclude_git:
      self.c.execute("SELECT categories.id as cat_id, categories.name as cat_name, short_name as license, filename FROM files JOIN licenses ON files.license_id = licenses.id JOIN categories ON licenses.category_id = categories.id WHERE scan_id = ? AND instr(filename, '/.git/') <= 0 ORDER BY cat_id, license, filename", [scan_id])
    else:
      self.c.execute("SELECT categories.id as cat_id, categories.name as cat_name, short_name as license, filename FROM files JOIN licenses ON files.license_id = licenses.id JOIN categories ON licenses.category_id = categories.id WHERE scan_id = ? ORDER BY cat_id, license, filename", [scan_id])
    res = self.c.fetchall()
    cats = {}
    for t in res:
      # scan through, creating categories and data structure as needed
      cat_id = t[0]
      cat_name = t[1]
      license = t[2]
      filename = t[3]

      cat = cats.get(cat_id, None)
      if not cat:
        # create tuple of category name, filename => license dict, and
        # license => count stats dict
        cats[cat_id] = (cat_name, {}, {})
        cat = cats.get(cat_id)

      # add filename and license to this category's list
      cat[1][filename] = license

      # insert or increment license count
      ccount = cat[2].get(license, 0)
      cat[2][license] = ccount + 1

    return cats

  # Get filename and corresponding license for all files for a given scan.
  # arguments:
  #   1) ID of scan
  #   2) (optional) if True, exclude files in any /.git/ subdirectory
  # returns: dict of filename => license, or None if error
  def getLicenseAndFilesForScan(self, scan_id, exclude_git=False):
    if exclude_git:
      self.c.execute("SELECT filename, short_name as license FROM files JOIN licenses ON files.license_id = licenses.id WHERE scan_id = ? AND instr(filename, '/.git/') <= 0 ORDER BY filename", [scan_id])
    else:
      self.c.execute("SELECT filename, short_name as license FROM files JOIN licenses ON files.license_id = licenses.id WHERE scan_id = ? ORDER BY filename", [scan_id])
    res = self.c.fetchall()
    files = {}
    for t in res:
      filename = t[0]
      license = t[1]
      files[filename] = license
    return files

  ########## CONFIG DATA FUNCTIONS ##########

  # Get all key/value pairs from the config table, including those specific
  # to spdxSummarizer (e.g. "magic", "version", etc.)
  # arguments: N/A
  # returns: a dict with all of the key/value pairs
  def getConfigData(self):
    self.c.execute("SELECT key, value FROM config")
    res = self.c.fetchall()
    config = {}
    for r in res:
      config[r[0]] = r[1]
    return config

  # Get all key/value pairs from the config table, _excluding_ those specific
  # to spdxSummarizer (e.g. "magic", "version", etc.)
  # arguments: N/A
  # returns: a dict with all of the key/value pairs
  def getConfigurableConfigData(self):
    self.c.execute("SELECT key, value FROM config")
    res = self.c.fetchall()
    config = {}
    for r in res:
      if r[0] not in self.internal_configs:
        config[r[0]] = r[1]
    return config

  # Get a value for a specific config key.
  # arguments:
  #   1) key string
  # returns: value for key if found, or None otherwise
  def getConfigForKey(self, key):
    self.c.execute("SELECT value FROM config WHERE key = ?", [key])
    res = self.c.fetchone()
    if not res:
      return None
    return res[0]

  # Set or update a config value.
  # Note: May not update core spdxSummarizer config values (magic, version or
  #   initialized).
  # arguments:
  #   1) key string
  #   2) value string
  #   3) commit: if True, commit updates at end
  # returns: True if successfully added to DB, False otherwise
  def setConfigValue(self, key, value, commit=True):
    if key in self.internal_configs:
      print(f"Error: can't use setConfigValue to change spdxSummarizer system key {key}.")
      return False
    try:
      self.c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", [key, value])
      if commit:
        self.conn.commit()
      return True
    except Exception as e:
      print(f'Error setting config key {key} => {value}: {str(e)}')
      return False
