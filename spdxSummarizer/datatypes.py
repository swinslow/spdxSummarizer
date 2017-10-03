# datatypes.py
#
# This module contains the primary data classes used by spdxSummarizer.
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

from sqlalchemy import create_engine
from sqlalchemy import Table, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Config(Base):
  __tablename__ = 'config'
  key = Column(String(), primary_key=True)
  value = Column(String())

  def __repr__(self):
    return f"Config {self.key} => {self.value}"

class Scan(Base):
  __tablename__ = 'scans'
  id = Column(Integer(), primary_key=True)
  scan_dt = Column(Date())
  desc = Column(String())

  def __repr__(self):
    return f"Scan {self.id}: {self.scan_dt}, {self.desc}"

  def asTuple(self):
    # FIXME in the future, consider keeping scan_dt as datetime.date
    return (self.id, str(self.scan_dt), self.desc)

class Category(Base):
  __tablename__ = 'categories'
  id = Column(Integer(), primary_key=True)
  name = Column(String())

  def __repr__(self):
    return f"Category {self.id}: {self.name}"

  def asTuple(self):
    return (self.id, self.name)

class License(Base):
  __tablename__ = 'licenses'
  # columns
  id = Column(Integer(), primary_key=True)
  short_name = Column(String())
  category_id = Column(Integer(), ForeignKey('categories.id'))
  # relationships
  category = relationship("Category", backref=backref('licenses', order_by=id))

  def __repr__(self):
    return f"License {self.id}: {self.short_name}, category {self.category.name}"

  def asTuple(self):
    return (self.id, self.short_name, self.category_id)

class File(Base):
  __tablename__ = 'files'
  # columns
  id = Column(Integer(), primary_key=True)
  scan_id = Column(Integer(), ForeignKey('scans.id'))
  filename = Column(String())
  license_id = Column(Integer(), ForeignKey('licenses.id'))
  sha1 = Column(String())
  md5 = Column(String())
  sha256 = Column(String())
  # relationships
  scan = relationship("Scan", backref=backref('files', order_by=id))
  license = relationship("License", backref=backref('files', order_by=id))

  def __repr__(self):
    return f"File {self.filename}, license: {self.license.short_name}"

  def asTuple(self):
    return (self.id, self.scan_id, self.filename, self.license_id,
      self.sha1, self.md5, self.sha256)

class Conversion(Base):
  __tablename__ = 'conversions'
  # columns
  id = Column(Integer(), primary_key=True)
  old_text = Column(String())
  new_license_id = Column(Integer(), ForeignKey('licenses.id'))
  # relationships
  new_license = relationship(
    "License",
    backref=backref('conversions', order_by=id)
  )

  def __repr__(self):
    return f"Conversion {self.id}: {self.old_text} => {self.new_license.short_name} ({self.new_license_id})"

  def asTuple(self):
    return (self.id, self.old_text, self.new_license_id)
