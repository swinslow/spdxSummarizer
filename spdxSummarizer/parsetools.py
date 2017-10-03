# parsetools.py
#
# This is a collection of functions to parse an SPDX tag:value file and
# extract filename and license info for more useful analyses or storage.
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
from operator import attrgetter
from enum import Enum

from spdxSummarizer.tvFileLoader import TVFileLoader

class FileData(object):
  def __init__(self):
    self.filename = ""
    self.license = ""
    self.sha1 = ""
    self.md5 = ""
    self.sha256 = ""

  def __str__(self):
    return f"FileData: {self.filename}, {self.license}"

# Parse an SPDX tag:value report and return a list of FileData for each
# parsed record found.
# arguments:
#    * report_filename: file path for SPDX tag:value report
# returns: list of FileData records, or null list if error or none found
def parseSPDXReport(report_filename):
  fds = []
  current_fd = None

  try:
    with open(report_filename, 'r') as f:
      # create a file loader object and start parsing lines into t/v pairs
      tvFileLoader = TVFileLoader()
      for line in f:
        tvFileLoader.parseNextLine(line)
      tvList = tvFileLoader.getFinalTVList()

      if tvList is None:
        print(f"Error: failed to load tag/value pairs from {report_filename}")
        return []

      # Now, walk through tag/value pair list. A "FileName" tag designates a
      # new file, and should trigger saving the prior fd and starting the
      # next one.
      for (tag, val) in tvList:
        if tag == "FileName":
          # start of data on a new file

          # finish and save old FileData if one was in process
          if current_fd is not None:
            fds.append(current_fd)

          # start a new FileData and save the filename
          current_fd = FileData()
          current_fd.filename = val

        elif tag == "LicenseConcluded":
          current_fd.license = val

        elif tag == "FileChecksum":
          # val should have an SHA1 tag/value pair
          # may also have MD5 and/or SHA256
          sp = val.split(":")
          if len(sp) != 2:
            print(f"Error: couldn't parse checksum tag/value in tag {tag}, value {val} for {current_fd.filename}")
            continue
          checksum = sp[1].strip()
          if sp[0] == "SHA1":
            current_fd.sha1 = checksum
          elif sp[0] == "MD5":
            current_fd.md5 = checksum
          elif sp[0] == "SHA256":
            current_fd.sha256 = checksum
          else:
            print(f"Error: invalid checksum type {sp[0]} in tag {tag}, value {val} for {current_fd.filename}")
            continue

        # we're ignoring other tags for the time being

      # when we get to the end, finish and save the final FileData that was
      # in process
      if current_fd is not None:
        fds.append(current_fd)

      # and return all FileData objects
      return fds

  except (IOError, OSError, FileNotFoundError) as e:
    print(f"Error opening or reading file: {str(e)}")
    return []

# Remove common prefix from a list of FileData objects.
# arguments:
#   * fds: list of FileData records produced by parseSPDXReport()
# returns: prefix string removed, or None if no common prefix or failed
def removePrefixes(fds):
  paths = [fd.filename for fd in fds]
  prefix = os.path.commonpath(paths)
  if paths != None and paths != '':
    for fd in fds:
      fd.filename = fd.filename[len(prefix):]
  return prefix
