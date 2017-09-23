# licenses.py
#
# This module contains functions for tracking known licenses and conversions,
# to maintain a common set in memory and in the database.
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

class FTCategory:
  def __init__(self, id, name, modified=False):
    super(FTCategory, self).__init__()
    self.id = id
    self.name = name
    self.modified = modified

  def __str__(self):
    return (f"FTCategory: ID {id}, {name}")

class FTLicense:
  def __init__(self, id, short_name, category_id, modified=False):
    super(FTLicense, self).__init__()
    self.id = id
    self.short_name = short_name
    self.category_id = category_id
    self.modified = modified

  def __str__(self):
    return (f"FTLicense: ID {id}, {short_name}, category {category_id}")

class FTConversion:
  def __init__(self, id, old_text, new_license_id, modified=False):
    super(FTConversion, self).__init__()
    self.id = id
    self.old_text = old_text
    self.new_license_id = new_license_id
    self.modified = modified

  def __str__(self):
    return (f"FTConversion: ID {id}, {old_text} => license {new_license_id}")

class FTLicenseStore:
  def __init__(self, db):
    super(FTLicenseStore, self).__init__()
    self.db = db
    self.licenses = {}
    self.conversions = {}
    self.categories = {}

  # Load all known licenses from the database, replacing the list currently 
  # in memory
  # arguments: N/A
  # returns: True if successfully loaded, False otherwise
  def loadLicensesFromDB(self):
    if not self.db:
      print("Database not loaded")
      return False
    
    # pull license data from database
    lics = self.db.getLicensesData()

    # clear old license data in memory and replace with database results
    self.licenses = {}
    for (id, short_name, category_id) in lics:
      lic = FTLicense(id, short_name, category_id, False)
      self.licenses[id] = lic

  # Load all known conversions from the database, replacing the list currently 
  # in memory
  # arguments: N/A
  # returns: True if successfully loaded, False otherwise
  def loadConversionsFromDB(self):
    if not self.db:
      print("Database not loaded")
      return False
    
    # pull license data from database
    convs = self.db.getConversionsData()

    # clear old conversion data in memory and replace with database results
    self.conversions = {}
    for (id, old_text, new_license_id) in convs:
      conv = FTConversion(id, old_text, new_license_id, False)
      self.conversions[id] = conv

  # Load all known categories from the database, replacing the list currently 
  # in memory
  # arguments: N/A
  # returns: True if successfully loaded, False otherwise
  def loadCategoriesFromDB(self):
    if not self.db:
      print("Database not loaded")
      return False

    # pull category data from database
    cats = self.db.getCategoriesData()

    # clear old category data in memory and replace with database results
    self.categories = {}
    for (id, name) in cats:
      cat = FTCategory(id, name, False)
      self.categories[id] = cat

  # Load all known categories, licenses and conversions from the database,
  # replacing the list currently in memory
  # arguments: N/A
  # returns: True if successfully loaded, False otherwise
  def loadAllFromDB(self):
    retval = self.loadCategoriesFromDB()
    if not retval:
      return False
    retval = self.loadLicensesFromDB()
    if not retval:
      return False
    retval = self.loadConversionsFromDB()
    if not retval:
      return False
    return True

  # get the ID corresponding to a license in memory
  # DOES NOT check the database -- just checks what's in memory
  # therefore, confirms first that the DB has been loaded
  # arguments:
  #   1) short text for license
  # returns: ID of license if found, -1 otherwise
  def getIDForLicense(self, short_name):
    if not self.db:
      print("Database not loaded")
      return -1

    for lic_id, lic in self.licenses.items():
      if lic.short_name == short_name:
        return lic_id

    return -1

  # get the license object with this ID
  # DOES NOT check the database -- just checks what's in memory
  # therefore, confirms first that the DB has been loaded
  # arguments:
  #   1) ID of license
  # returns: FTLicense object with this ID if found, None otherwise
  def getLicense(self, id):
    if not self.db:
      print("Database not loaded")
      return None
    return self.licenses.get(id, None)

  # get the ID corresponding to a conversion in memory
  # DOES NOT check the database -- just checks what's in memory
  # therefore, confirms first that the DB has been loaded
  # arguments:
  #   1) old text for conversion
  # returns: ID of _conversion_  (NOT license) if found, -1 otherwise
  def getIDForConversion(self, old_text):
    if not self.db:
      print("Database not loaded")
      return -1

    for conv_id, conv in self.conversions.items():
      if conv.old_text == old_text:
        return conv_id

    return -1

  # get the conversion object with this ID
  # DOES NOT check the database -- just checks what's in memory
  # therefore, confirms first that the DB has been loaded
  # arguments:
  #   1) ID of conversion
  # returns: FTConversion object with this ID if found, None otherwise
  def getConversion(self, id):
    if not self.db:
      print("Database not loaded")
      return None
    return self.conversions.get(id, None)

  # get the highest ID currently in use for any category
  # arguments: N/A
  # returns: integer ID of highest category ID in use, or None if error
  def getHighestCategoryID(self):
    if not self.db:
      print("Database not loaded")
      return None
    max_id = 0
    for id, x in self.categories.items():
      if (id > max_id):
        max_id = id
    return max_id

  # get the highest ID currently in use for any license
  # arguments: N/A
  # returns: integer ID of highest license ID in use, or None if error
  def getHighestLicenseID(self):
    if not self.db:
      print("Database not loaded")
      return None
    max_id = 0
    for id, x in self.licenses.items():
      if (id > max_id):
        max_id = id
    return max_id

  # get the highest ID currently in use for any conversion
  # arguments: N/A
  # returns: integer ID of highest conversion ID in use, or None if error
  def getHighestConversionID(self):
    if not self.db:
      print("Database not loaded")
      return None
    max_id = 0
    for id, x in self.conversions.items():
      if (id > max_id):
        max_id = id
    return max_id

  # Create new conversion in memory, so that it can be added to database
  # when ready to import
  # Pulls max_id from license store.
  # arguments:
  #   1) old_text: old license text to map
  #   2) new_license_id: existing license ID to map to
  # returns: temporary new Conversion ID if created, or None if error
  def createConversionInStore(self, old_text, new_license_id):
    max_id = self.getHighestConversionID()
    if not max_id:
      print("Couldn't get highest conversion ID")
      return None
    conv_id = max_id + 1
    # create new Conversion and mark as modified, since we need to
    # save it out to the database later
    conv = FTConversion(conv_id, old_text, new_license_id, True)
    self.conversions[conv_id] = conv
    return conv_id

  # Create new category in memory, so that it can be added to database
  # when ready to import
  # Pulls max_id from license store.
  # arguments:
  #   1) name: name of new category
  # returns: temporary new Category ID if created, or None if error
  def createCategoryInStore(self, name):
    max_id = self.getHighestCategoryID()
    if not max_id:
      print("Couldn't get highest category ID")
      return None
    cat_id = max_id + 1
    # create new Category and mark as modified, since we need to
    # save it out to the database later
    cat = FTCategory(cat_id, name, True)
    self.categories[cat_id] = cat
    return cat_id

  # Create new license in memory, so that it can be added to database
  # when ready to import
  # Pulls max_id from license store.
  # arguments:
  #   1) short_name: name of new license
  #   2) category_id: category ID
  # returns: temporary new License ID if created, or None if error
  def createLicenseInStore(self, short_name, category_id):
    max_id = self.getHighestLicenseID()
    if not max_id:
      print("Couldn't get highest license ID")
      return None
    lic_id = max_id + 1
    # create new License and mark as modified, since we need to
    # save it out to the database later
    lic = FTLicense(lic_id, short_name, category_id, True)
    self.licenses[lic_id] = lic
    return lic_id

  # Save all modified items out to database.
  # If any errors, roll back and return False.
  # arguments: N/A
  # returns: True if successful, False otherwise
  def saveAllModifiedToDatabase(self):
    # categories first
    for cat_id, ftcat in self.categories.items():
      if ftcat.modified:
        retval = self.db.addNewCategory(ftcat.name, False, cat_id)
        if retval == cat_id:
          print(f"Saved category {cat_id} ({ftcat.name}) to database.")
        else:
          print(f"Error: Couldn't save category {cat_id} ({ftcat.name}) to database; rolling back.")
          self.db.rollbackChanges()
          return False

    # licenses next
    for lic_id, ftlic in self.licenses.items():
      if ftlic.modified:
        retval = self.db.addNewLicense(ftlic.short_name, ftlic.category_id,
          False, lic_id)
        if retval == lic_id:
          print(f"Saved license {lic_id} ({ftlic.short_name}) to database.")
        else:
          print(f"Error: Couldn't save license {lic_id} ({ftlic.short_name}) to database; rolling back.")
          self.db.rollbackChanges()
          return False

    # conversions last
    for conv_id, ftconv in self.conversions.items():
      if ftconv.modified:
        retval = self.db.addNewConversion(ftconv.old_text,
          ftconv.new_license_id, False, conv_id)
        if retval == conv_id:
          print(f"Saved conversion {ftconv.old_text} => {ftconv.new_license_id} to database.")
        else:
          print(f"Error: Couldn't save conversion {ftconv.old_text} => {ftconv.new_license_id} to database; rolling back.")
          self.db.rollbackChanges()
          return False

    return True

  ########## APPLYING CONVERSIONS AND LICENSES ##########

  # Given a list of licenses, apply known conversions and license IDs,
  # and return a data struct that indicates which ones are still pending.
  # arguments:
  #   1) lics: list of license text names
  # returns: dict of {"ldict" => licenses dict; "lpending" => pending texts}
  #   licenses dict: {old lic name => tuple of (license ID, new lic name)}
  #   example: {"NOASSERTION" => (30, "No License Found")}
  def runExistingConversionsAndLicenses(self, lics):

    # 1) generate in-memory license dict from license list
    #      {old lic text => tuple(new license id, "new license text")}
    # all "new license ids" are set at -1 initially, and filled in as we
    # confirm that licenses and conversions have been added as needed

    # de-duplicate the list and convert it to a dict in the format above
    # also strip out "LicenseRef-" from all new license texts
    ldict = {}
    for lic in list(set(lics)):
      new_lic = lic.replace("LicenseRef-", "")
      ldict[lic] = (-1, new_lic)

    # 2) implement existing conversions
    for old_text, (new_id, new_license_text) in ldict.items():
      conv_id = self.getIDForConversion(new_license_text)
      if (conv_id != -1):
        conv = self.getConversion(conv_id)
        lic = self.getLicense(conv.new_license_id)
        ldict[old_text] = (lic.id, lic.short_name)

    # 3) now fill in license ID #'s for all known pending licenses
    for old_text, (new_id, new_license_text) in ldict.items():
      if new_id == -1:
        lic_id = self.getIDForLicense(new_license_text)
        if lic_id != -1:
          ldict[old_text] = (lic_id, new_license_text)

    # 4) check to see if there are any licenses that we don't know yet
    lpending = {}
    for old_text, (new_id, new_license_text) in ldict.items():
      if new_id == -1:
        lpending[old_text] = new_license_text

    # finally, package ldict and lpending together, and return them
    return {"ldict": ldict, "lpending": lpending}
