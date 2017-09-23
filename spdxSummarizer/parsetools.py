# parsetools.py
#
# This is a collection of functions to parse an SPDX tag:value file exported
# from Fossology, and to convert it to an in-memory format for more useful
# analyses or storage.
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

class FileData(object):
  def __init__(self, filename, license, md5, sha1):
    self.filename = filename
    self.license = license
    self.md5 = md5
    self.sha1 = sha1

  def __str__(self):
    return f"FileData: {self.filename}, {self.license}, {self.md5}, {self.sha1}"

class ParserState(Enum):
  # READY means we haven't yet found any ##File tags
  # so we'll just skip lines until we find the first one.
  # when we do, enter the IN_FILE_SET state.
  READY = 1

  # IN_FILE_SET means we're currently scanning a file set
  # so we'll parse key:value tags into the current FileData object,
  # and upon hitting the next ##File tag we'll start a new one.
  # when we hit "##-------------------------", enter the DONE state.
  IN_FILE_SET = 2

  # DONE means we've finished parsing the ##File records.
  DONE = 3

# Parse an SPDX tag:value report exported from Fossology, and return
# a list of FileData for each parsed record found.
# arguments:
#    * report_filename: file path for SPDX Fossology tag:value report
# returns: list of FileData records, or null list if error or none found
def parseFossologySPDXReport(report_filename):
  try:
    with open(report_filename, 'r') as f:
      state = ParserState.READY
      tagdict = {}
      fds = []

      for line in f:
        line = line.strip()

        # if we're in READY state, just scan until we hit the first ##File tag
        if state == ParserState.READY:
          if line == "##File":
            # found it; enter new state
            state = ParserState.IN_FILE_SET
            continue

        # if we're in IN_FILE_SET state, now we're parsing tags
        if state == ParserState.IN_FILE_SET:
          # flags for next action
          end_current_record = False
          switch_to_done = False

          # skip blank lines (we've already stripped whitespace)
          if line == "":
            continue

          # if we see a new "##File" tag, we're done with the current record
          if line == "##File":
            end_current_record = True

          # if we see a "##-------------------------" line, we're 
          # completely done
          if line == "##-------------------------":
            end_current_record = True
            switch_to_done = True

          # otherwise, parse the current line as a tag:value pair
          # only split once; any subsequent colons go into the value
          if not end_current_record and not switch_to_done:
            result = line.split(':', 1)
            if len(result) == 2:
              k = result[0].strip()
              v = result[1].strip()

              # check here to see if the value is a <text></text> multiline
              if v.startswith("<text>") and not v.endswith("</text>"):
                # scan and append subsequent lines until we hit one
                # that ends with </text>
                found_end_tag = False
                while not found_end_tag:
                  nextline = next(f).strip()
                  v = v + nextline
                  if nextline.endswith("</text>"):
                    found_end_tag = True

              # value in dict will be list of identified values
              # if already found this tag, append to existing list
              if tagdict.get(k):
                tagdict[k].append(v)
              else:
                tagdict[k] = [v]
            else:
              print(f"Error: found line {line}")

          # now, close out current record if needed
          if end_current_record:
            # extract the interesting data and build a record
            filename_list = tagdict.get("FileName")
            if (filename_list):
              filename = ";".join(filename_list)
            else:
              filename = None

            lic_concluded_list = tagdict.get("LicenseConcluded")
            if (lic_concluded_list):
              lic_concluded = ";".join(lic_concluded_list)
            else:
              lic_concluded = None

            # MD5 and SHA1 are lumped together within FileChecksum
            # so we need to extract them
            cs_sha1 = None
            cs_md5 = None
            checksums = tagdict.get("FileChecksum")
            for checksum_str in checksums:
              # split again and check tag
              cs = checksum_str.split(':', 1)
              if len(cs) == 2:
                cs_type = cs[0].strip()
                cs_value = cs[1].strip()
                if (cs_type == "SHA1"):
                  cs_sha1 = cs_value
                elif (cs_type == "MD5"):
                  cs_md5 = cs_value
                else:
                  print(f"Error: got unknown checksum type {cs_type} in checksum string {checksum_str}")
              else:
                print(f"Error: couldn't parse checksum string {checksum_str}")

            fd = FileData(
              filename,
              lic_concluded,
              cs_md5,
              cs_sha1
            )

            # add the record to the list of all files
            fds.append(fd)

            # finally, reset for new file record
            tagdict = {}

          # finally, if we're done parsing, then break out
          if switch_to_done:
            state = ParserState.DONE
            break;

      # done parsing the file
      return fds

  except (IOError, OSError, FileNotFoundError) as e:
    print(f"Error opening or reading file: {str(e)}")
    return []

# Remove common prefix from a list of FileData objects.
# arguments:
#   * fds: list of FileData records produced by parseFossologySPDXReport()
# returns: prefix string removed, or None if no common prefix or failed
def removePrefixes(fds):
  paths = [fd.filename for fd in fds]
  prefix = os.path.commonpath(paths)
  if paths != None and paths != '':
    for fd in fds:
      fd.filename = fd.filename[len(prefix):]
  return prefix
