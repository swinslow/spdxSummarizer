# tests/test_dbtools.py
#
# Contains unit tests for the functionality in dbtools.py.
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

import unittest

from spdxSummarizer import dbtools

class DBToolsTestSuite(unittest.TestCase):
  """spdxSummarizer database tools test suite."""

  def setUp(self):
    # create and initialize an in-memory database
    self.db = dbtools.FTDatabase()
    self.db.createDatabase(":memory:")

    # test config file contains config, categories, licenses and conversions
    # FIXME also this path probably shouldn't be built in this way
    self.db.initializeDatabaseTables("tests/test_config.json")

    # also import some basic scans and files
    self.insertSampleScanData()

  def tearDown(self):
    self.db.closeDatabase()
    self.db = None

  def insertSampleScanData(self):
    self.db.c.execute('''INSERT INTO scans (id, scan_dt, desc) VALUES
      (1, "2017-01-01", "test scan 1"),
      (8, "2017-08-08", "test scan 8"),
      (3, "2017-03-03", "test scan 3"),
      (2, "2017-02-02", "test scan 2")
      ''')

  ########## TESTS BELOW HERE ##########

  def test_smoke(self):
    assert True

  ##### Database initialization

  def test_db_is_initialized(self):
    # main database should be initialized
    self.assertTrue(self.db.isInitialized())

  def test_empty_db_is_not_initialized(self):
    # a brand new database shouldn't be initialized
    new_db = dbtools.FTDatabase()
    self.assertFalse(new_db.isInitialized())
    # and an opened but empty database shouldn't be initialized
    new_db.createDatabase(":memory:")
    self.assertFalse(new_db.isInitialized())

  ##### Scan data

  def test_can_get_list_of_scan_ids(self):
    scan_ids = self.db.getScansIDList()
    self.assertIsInstance(scan_ids, list)
    self.assertIn(1, scan_ids)
    self.assertIn(2, scan_ids)
    self.assertIn(3, scan_ids)
    self.assertIn(8, scan_ids)

  def test_list_of_scan_ids_is_sorted(self):
    scan_ids = self.db.getScansIDList()
    last_id = 0
    for id in scan_ids:
      self.assertGreater(id, last_id)
      last_id = id

  def test_can_get_full_scans_data(self):
    scans = self.db.getScansData()
    # should be list of tuples of form (id, scan_dt, desc)
    self.assertIsInstance(scans, list)
    self.assertIsInstance(scans[0], tuple)
    self.assertIsInstance(scans[0][0], int)
    self.assertIsInstance(scans[0][1], str)
    self.assertIsInstance(scans[0][2], str)
    self.assertEqual(len(scans), 4)
    self.assertEqual(scans[0][0], 1)
    self.assertEqual(scans[0][1], "2017-01-01")
    self.assertEqual(scans[0][2], "test scan 1")

  def test_list_of_scans_is_sorted_by_id(self):
    scans = self.db.getScansData()
    last_id = 0
    for (id, scan_dt, desc) in scans:
      self.assertGreater(id, last_id)
      last_id = id

  def test_can_get_single_scan_data(self):
    scan = self.db.getScanData(8)
    # should be tuple of form (id, scan_dt, desc)
    self.assertIsInstance(scan, tuple)
    self.assertIsInstance(scan[0], int)
    self.assertIsInstance(scan[1], str)
    self.assertIsInstance(scan[2], str)
    self.assertEqual(scan[0], 8)
    self.assertEqual(scan[1], "2017-08-08")
    self.assertEqual(scan[2], "test scan 8")

  def test_invalid_single_scan_id_returns_none(self):
    scan = self.db.getScanData(99)
    self.assertIsNone(scan)

  def test_can_add_and_retrieve_new_scan(self):
    scan_id = self.db.addNewScan("2018-01-01")
    self.assertGreater(scan_id, 0)
    scan = self.db.getScanData(scan_id)
    # should be tuple of form (id, scan_dt, desc)
    self.assertIsInstance(scan, tuple)
    self.assertIsInstance(scan[0], int)
    self.assertIsInstance(scan[1], str)
    self.assertIsInstance(scan[2], str)
    # id should be 9 since we've inserted a scan 8 above
    self.assertEqual(scan[0], 9)
    self.assertEqual(scan[1], "2018-01-01")
    self.assertEqual(scan[2], "no description")

  def test_can_add_and_rollback_a_scan(self):
    scan_id = self.db.addNewScan("2018-01-01", "to be rolled back", False)
    self.assertGreater(scan_id, 0)
    self.db.rollbackChanges()
    scan = self.db.getScanData(scan_id)
    self.assertIsNone(scan)

  def test_cannot_add_new_scan_to_uninitialized_db(self):
    new_db = dbtools.FTDatabase()
    new_db.createDatabase(":memory:")
    scan_id = new_db.addNewScan("2018-01-01", "should fail", False)
    self.assertEqual(scan_id, -1)

  ##### Category data

  def test_can_get_list_of_category_ids(self):
    category_ids = self.db.getCategoriesIDList()
    self.assertIsInstance(category_ids, list)
    self.assertIn(1, category_ids)
    self.assertIn(7, category_ids)
    self.assertNotIn(8, category_ids)

  def test_list_of_category_ids_is_sorted(self):
    category_ids = self.db.getCategoriesIDList()
    last_id = 0
    for id in category_ids:
      self.assertGreater(id, last_id)
      last_id = id

  def test_can_get_full_categories_data(self):
    categories = self.db.getCategoriesData()
    # should be list of tuples of form (id, name)
    self.assertIsInstance(categories, list)
    self.assertIsInstance(categories[0], tuple)
    self.assertIsInstance(categories[0][0], int)
    self.assertIsInstance(categories[0][1], str)
    self.assertEqual(len(categories), 7)
    self.assertEqual(categories[0][0], 1)
    self.assertEqual(categories[0][1], "Project licenses")

  def test_list_of_categories_is_sorted_by_id(self):
    categories = self.db.getCategoriesData()
    last_id = 0
    for (id, name) in categories:
      self.assertGreater(id, last_id)
      last_id = id

  def test_can_get_single_category_data(self):
    category = self.db.getCategoryData(3)
    # should be tuple of form (id, name)
    self.assertIsInstance(category, tuple)
    self.assertIsInstance(category[0], int)
    self.assertIsInstance(category[1], str)
    self.assertEqual(category[0], 3)
    self.assertEqual(category[1], "Copyleft")

  def test_invalid_single_category_id_returns_none(self):
    category = self.db.getCategoryData(99)
    self.assertIsNone(category)

if __name__ == "__main__":
  unittest.main()
