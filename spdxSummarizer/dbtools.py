# dbtools.py
#
# This module contains the SPDatabase class, for interacting with a SQLite
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

import json
import os
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from spdxSummarizer.spconfig import SPVERSION
from spdxSummarizer.datatypes import Base
from spdxSummarizer.datatypes import Config, Scan, Category, License, File, \
  Conversion

class SPDatabase(object):
  def __init__(self):
    super(SPDatabase, self).__init__()
    self.engine = None
    self.session = None
    self.internal_configs = ["magic", "initialized", "version"]

  def closeDatabase(self):
    if self.session is not None:
      self.session.close()
      self.session = None
    self.engine = None

  # create new uninitialized spdxSummarizer database
  # WARNING: will delete the specified DB file if it already exists
  # arguments:
  #   1) db_filename: string with path to database file
  # returns: True on success, False on failure
  def createDatabase(self, db_filename):
    if db_filename != ":memory:":
      # delete file if it already exists
      if os.path.exists(db_filename):
        try:
          os.remove(db_filename)
        except PermissionError as e:
          errstr = str(e)
          print(f"{db_filename} exists and can't be deleted: {errstr}")
          return False
    engine_str = "sqlite:///" + db_filename

    # connect to (e.g. create) database
    self.engine = create_engine(engine_str)
    # FIXME check for errors
    Session = sessionmaker(bind=self.engine)
    self.session = Session()

    # create tables
    Base.metadata.create_all(self.engine)

    # insert basic beginner config values
    c1 = Config(key="magic", value="spdxSummarizer")
    c2 = Config(key="initialized", value="no")
    self.session.bulk_save_objects([c1, c2])
    self.session.commit()
    return True

  # open connection to existing spdxSummarizer database, and confirm
  # that it is a valid spdxSummarizer database
  # arguments:
  #   1) db_filename: string with path to database file
  # returns: True on success, False on failure
  def openDatabase(self, db_filename):
    # don't accept :memory: here; only open existing DBs
    if os.path.exists(db_filename):
      # connect to (e.g. create) database
      engine_str = "sqlite:///" + db_filename
      self.engine = create_engine(engine_str)
      # FIXME check for errors
      Session = sessionmaker(bind=self.engine)
      self.session = Session()

      # query for config magic value
      try:
        query = self.session.query(Config).filter_by(key="magic").first()
        if query.value == "spdxSummarizer":
          # we're good
          return True
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
    self.session.commit()

  # Roll back changes to database since last commit.  Typically called when
  # encountering an error during e.g. a set of calls to addNewFile().
  # arguments: N/A
  # returns: N/A
  def rollbackChanges(self):
    self.session.rollback()

  # Initialize config table based on dict already read from JSON file.
  # arguments:
  #   1) config_dict: dictionary with key/value config strings
  # returns: True if successful, False on error
  def initializeConfigTable(self, config_dict):
    configs = []
    for (key, value) in config_dict.items():
      c = Config(key=key, value=value)
      configs.append(c)
    self.session.bulk_save_objects(configs)
    self.session.commit()
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
      category = Category(id=cid, name=cname)
      self.session.add(category)

      # now, walk through licenses list and add each to licenses table
      # note that we might legitimately not have any licenses for 
      # a given category
      for license in licenses:
        lic = License(short_name=license, category_id=cid)
        self.session.add(lic)

    self.session.commit()
    return True

  # Initialize conversions tables based on dict already read from JSON file.
  # arguments:
  #   1) conversions_dict: dict of conversion objects
  # returns: True if successful, False on error
  def initializeConversionsTable(self, conversions_dict):
    # walk through and parse each conversion key/value pair
    for (old_text, new_license) in conversions_dict.items():
      # look up ID for new license text
      lic = self.session.query(License).filter(License.short_name == new_license).first()
      if lic != None:
        conversion = Conversion(old_text=old_text, new_license_id=lic.id)
        self.session.add(conversion)
      else:
        print(f"Couldn't find license ID in database for {old_text}: {new_license}")
        return False

    self.session.commit()
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
        query = self.session.query(Config).filter(Config.key == "initialized")
        query.update({Config.value: "yes"})
        c = Config(key="version", value=SPVERSION)
        self.session.add(c)

        self.session.commit()
        return True

    # FIXME check for file not found as separate exception?
    except json.decoder.JSONDecodeError as e:
      print(f'Error loading or parsing {json_filename}: {str(e)}')
      return False

  ########## CONFIG DATA FUNCTIONS ##########

  # Return boolean for whether the DB was fully initialized.
  # arguments: N/A
  # returns: True if "initialized" in config is "yes", False otherwise
  def isInitialized(self):
    if not self.engine or not self.session:
      return False

    query = self.session.query(Config).filter(Config.key == "initialized").first()
    return (query is not None and query.value == "yes")

  ########## SCAN DATA FUNCTIONS ##########

  # Get a list of IDs for all prior scans.
  # arguments: N/A
  # returns: list of IDs from all scans in database
  def getScansIDList(self):
    scans = self.session.query(Scan.id).order_by(Scan.id)
    return [scan.id for scan in scans]

  ##### FIXME HERE AND BELOW -- for now, keep as tuples.
  ##### FIXME will make sure transition to SQLAlchemy works as expected,
  ##### FIXME then start converting rest of spdxSummarizer to using the
  ##### FIXME new data types.

  # Get all data for all prior scans.
  # arguments: N/A
  # returns: list of data tuples from all scans in database
  #   tuple format: (id, scan_dt, desc)
  def getScansData(self):
    scans = self.session.query(Scan).order_by(Scan.id)
    scanList = []
    for scan in scans:
      scanList.append(scan.asTuple())
    return scanList

  # Get all data for prior scan with given ID.
  # arguments:
  #   1) ID of prior scan
  # returns: tuple of data if found or None if not found
  #   tuple format: (id, scan_dt, desc)
  def getScanData(self, scan_id):
    scan = self.session.query(Scan).filter(Scan.id == scan_id).first()
    if scan is not None:
      return scan.asTuple()
    else:
      return None

  # Add new scan to database.
  # arguments:
  #   1) scan date
  #   2) description (optional)
  #   3) commit: if True, commit updates at end
  # returns: new ID for scan if successfully added to DB, or -1 otherwise
  def addNewScan(self, scan_dt_str, desc="no description", commit=True):
    try:
      # FIXME in future, may require scan_dt as datetime.date object
      scan_dt_datetime = datetime.datetime.strptime(scan_dt_str, "%Y-%m-%d")
      scan_dt = scan_dt_datetime.date()
      scan = Scan(scan_dt=scan_dt, desc=desc)
      self.session.add(scan)
      if commit:
        self.session.commit()
      else:
        self.session.flush()
      return scan.id
    except Exception as e:
      print(f'Error adding new scan {desc}: {str(e)}')
      return -1

  ########## CATEGORY DATA FUNCTIONS ##########

  # Get a list of IDs for all known categories.
  # arguments: N/A
  # returns: list of IDs from all categories in database
  def getCategoriesIDList(self):
    cats = self.session.query(Category.id).order_by(Category.id)
    return [cat.id for cat in cats]

  # Get all data for all known categories.
  # arguments: N/A
  # returns: list of data tuples from all categories in database
  #   tuple format: (id, name)
  def getCategoriesData(self):
    cats = self.session.query(Category).order_by(Category.id)
    catList = []
    for cat in cats:
      catList.append(cat.asTuple())
    return catList

  # Get all data for known category with given ID.
  # arguments:
  #   1) ID of category
  # returns: tuple of data if found or None if not found
  #   tuple format: (id, name)
  def getCategoryData(self, category_id):
    cat = self.session.query(Category).filter(Category.id == category_id).first()
    if cat is not None:
      return cat.asTuple()
    else:
      return None

  # Add new category to database.
  # arguments:
  #   1) name for category
  #   2) commit: if True, commit updates at end
  #   3) id: if non-zero, use this for new ID
  # returns: new ID for category if successfully added to DB, or -1 otherwise
  def addNewCategory(self, name, commit=True, id=0):
    try:
      if id == 0:
        cat = Category(name=name)
      else:
        cat = Category(id=id, name=name)
      self.session.add(cat)
      if commit:
        self.session.commit()
      else:
        self.session.flush()
      return cat.id
    except Exception as e:
      print(f'Error adding new category {name}: {str(e)}')
      return -1

  ########## LICENSE DATA FUNCTIONS ##########

  # Get a list of IDs for all known licenses.
  # arguments: N/A
  # returns: list of IDs from all licenses in database
  def getLicensesIDList(self):
    lics = self.session.query(License.id).order_by(License.id)
    return [lic.id for lic in lics]

  # Get all data for all known licenses.
  # arguments: N/A
  # returns: list of data tuples from all licenses in database
  #   tuple format: (id, short_name, category_id)
  def getLicensesData(self):
    lics = self.session.query(License).order_by(License.id)
    licList = []
    for lic in lics:
      licList.append(lic.asTuple())
    return licList

  # Get all data for known license with given ID.
  # arguments:
  #   1) ID of license
  # returns: tuple of data if found or None if not found
  #   tuple format: (id, short_name, category_id)
  def getLicenseData(self, license_id):
    lic = self.session.query(License).filter(License.id == license_id).first()
    if lic is not None:
      return lic.asTuple()
    else:
      return None

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
        lic = License(short_name=short_name, category_id=category_id)
      else:
        lic = License(id=id, short_name=short_name, category_id=category_id)
      self.session.add(lic)
      if commit:
        self.session.commit()
      else:
        self.session.flush()
      return lic.id
    except Exception as e:
      print(f'Error adding new license {short_name}: {str(e)}')
      return -1

  ########## CONVERSION DATA FUNCTIONS ##########

  # Get a list of IDs for all known conversions.
  # arguments: N/A
  # returns: list of IDs from all conversions in database
  def getConversionsIDList(self):
    convs = self.session.query(Conversion.id).order_by(Conversion.id)
    return [conv.id for conv in convs]

  # Get all data for all known conversions.
  # arguments: N/A
  # returns: list of data tuples from all conversions in database
  #   tuple format: (id, old_text, new_license_id)
  def getConversionsData(self):
    convs = self.session.query(Conversion).order_by(Conversion.id)
    convList = []
    for conv in convs:
      convList.append(conv.asTuple())
    return convList

  # Get all data for known conversions with given ID.
  # arguments:
  #   1) ID of conversions
  # returns: tuple of data if found or None if not found
  #   tuple format: (id, old_text, new_license_id)
  def getConversionData(self, conversion_id):
    conv = self.session.query(Conversion).filter(Conversion.id == conversion_id).first()
    if conv is not None:
      return conv.asTuple()
    else:
      return None

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
        conv = Conversion(old_text=old_text, new_license_id=new_license_id)
      else:
        conv = Conversion(id=id, old_text=old_text, new_license_id=new_license_id)
      self.session.add(conv)
      if commit:
        self.session.commit()
      else:
        self.session.flush()
      return conv.id
    except Exception as e:
      print(f'Error adding new conversion {old_text}: {str(e)}')
      return -1

  ########## FILE DATA FUNCTIONS ##########

  # Get all data for file with given ID.
  # arguments:
  #   1) ID of file
  # returns: tuple of data if found or None if not found
  #   tuple format: (id, scan_id, filename, license_id, md5, sha1)
  def getFileData(self, file_id):
    file = self.session.query(File).filter(File.id == file_id).first()
    if file is not None:
      return file.asTuple()
    else:
      return None

  # Get all data for file with given scan ID and filename.
  # arguments:
  #   1) ID of scan
  #   2) filename
  # returns: tuple of data if found or None if not found
  #   tuple format: (id, scan_id, filename, license_id, md5, sha1)
  def getFileInstanceData(self, scan_id, filename):
    file = self.session.query(File).filter(
      and_(
        File.filename == filename,
        File.scan_id == scan_id
      )
    ).first()
    if file is not None:
      return file.asTuple()
    else:
      return None

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
      file = File(scan_id=scan_id, filename=filename, license_id=license_id,
        md5=md5, sha1=sha1)
      self.session.add(file)
      if commit:
        self.session.commit()
      else:
        self.session.flush()
      return file.id
    except Exception as e:
      print(f'Error adding new file {filename}: {str(e)}')
      return -1

  # Add bulk list of new files to database.
  # arguments:
  #   1) scan ID
  #   2) list of tuples in format:
  #      (filename, ID of license, MD5 string, SHA1 string)
  #   3) commit: if True, commit updates at end
  # returns: True if successfully added to DB, False otherwise
  # NOTE that scan and license IDs are foreign key constraints, so those must
  #      be added prior to adding a file that references them
  def addBulkNewFiles(self, scan_id, file_tuples, commit=True):
    try:
      files = []
      for ft in file_tuples:
        file = File(
          scan_id=scan_id,
          filename=ft[0],
          license_id=ft[1],
          md5=ft[2],
          sha1=ft[3]
        )
        files.append(file)
      self.session.bulk_save_objects(files)
      if commit:
        self.session.commit()
      else:
        self.session.flush()
      return True
    except Exception as e:
      print(f'Error adding bulk new files for scan {scan_id}: {str(e)}')
      return False

  ########## COMBO DATA FUNCTIONS ##########

  # Get file and license info, by category, for all files for a given scan.
  # arguments:
  #   1) ID of scan
  #   2) (optional) if True, exclude files in any /.git/ subdirectory
  # returns: dict of category =>
  #    (category_name, {filename => license}, {license => count})
  #   or None if error
  def getCategoryFilesForScan(self, scan_id, exclude_git=False):
    query = self.session.query(
      Category.id, Category.name, File.filename, License.short_name
    ).join(License).join(File)
    query = query.filter(File.scan_id == scan_id)
    if exclude_git:
      query = query.filter(~(File.filename.contains('/.git/')))
    query = query.order_by(Category.id, License.short_name, File.filename)

    cats = {}
    for q in query:
      # scan through, creating categories and data structure as needed
      cat_id = q[0]
      cat_name = q[1]
      filename = q[2]
      license = q[3]

      cat = cats.get(cat_id, None)
      if cat is None:
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
    query = self.session.query(File.filename, License.short_name).\
      join(License).\
      filter(File.scan_id == scan_id)
    if exclude_git:
      query = query.filter(~(File.filename.contains('/.git/')))
    query = query.order_by(File.filename)

    files = {}
    for q in query:
      filename = q[0]
      license = q[1]
      files[filename] = license
    return files

  ########## CONFIG DATA FUNCTIONS ##########

  # Get all key/value pairs from the config table, including those specific
  # to spdxSummarizer (e.g. "magic", "version", etc.)
  # arguments: N/A
  # returns: a dict with all of the key/value pairs
  def getConfigData(self):
    configs = self.session.query(Config)
    configDict = {}
    for config in configs:
      configDict[config.key] = config.value
    return configDict

  # Get all key/value pairs from the config table, _excluding_ those specific
  # to spdxSummarizer (e.g. "magic", "version", etc.)
  # arguments: N/A
  # returns: a dict with all of the key/value pairs
  def getConfigurableConfigData(self):
    configDict = self.getConfigData()
    for k in self.internal_configs:
      try:
        del configDict[k]
      except KeyError:
        pass
    return configDict

  # Get a value for a specific config key.
  # arguments:
  #   1) key string
  # returns: value for key if found, or None otherwise
  def getConfigForKey(self, key):
    config = self.session.query(Config).filter(key == key).first()
    try:
      return config.value
    except AttributeError:
      return None

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
      try:
        query = self.session.query(Config)
        config = query.filter(Config.key == key).first()
        config.value = value
      except AttributeError:
        config = Config(key=key, value=value)
        self.session.add(config)
      if commit:
        self.session.commit()
      else:
        self.session.flush()
      return True
    except Exception as e:
      print(f'Error setting config for {key}: {str(e)}')
      return False
