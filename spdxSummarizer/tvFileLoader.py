# tvFileLoader.py
#
# This file loads a series of tag/value pairs from a file, in preparation for
# parsing as SPDX data (in a subsequent stage).
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

from enum import Enum

class TVFileLoaderState(Enum):
  # ready to parse new tag/value pair
  READY = 1
  # in the middle of parsing a multi-line <text> value
  MIDTEXT = 2
  # encountered an error from which we can't recover
  ERROR = 99

class TVFileLoader:
  def __init__(self, log_func=print):
    # log_func should be a logger function that takes a single
    # string and logs it wherever it ought to go
    super(TVFileLoader, self).__init__()
    self.log_func = log_func
    self.reset()

  def reset(self):
    self.loaderState = TVFileLoaderState.READY
    self.tvList = []
    self.currentLineNum = 0
    self.currentTag = ""
    self.currentValue = ""

  ########## PARSER HELPER FUNCTIONS ##########
  def _parseResetTagValue(self):
    self.currentTag = ""
    self.currentValue = ""

  def _parseNextLineFromMidtext(self, line):
    # if we're currently parsing a multi-line <text> value, then
    # just look for the </text> tag
    endTagLoc = line.find("</text>")
    if endTagLoc == -1:
      # not found, keep going
      self.currentValue += line + "\n"
    else:
      # found tag => end the multi-line value
      self.currentValue += line[0:endTagLoc]
      # push the new tag/value pair onto the list
      t = (self.currentTag, self.currentValue)
      self.tvList.append(t)
      # clean up and proceed
      self._parseResetTagValue()
      self.loaderState = TVFileLoaderState.READY

  def _parseNextLineFromReady(self, line):
    # FIXME is there a reason we shouldn't strip whitespace first?
    # FIXME if removed, be sure to modify checks below
    line = line.strip()

    # skip if it's a blank line
    if line == "":
      return

    # skip if it's a comment
    if line.startswith("#"):
      return

    # otherwise, start parsing a new tag/value entry
    colonLoc = line.find(":")
    if colonLoc == -1:
      # didn't find a colon; this is an error
      self.log_func(f"Error: didn't find ':' in line {self.currentLineNum}, {line}")
      self.log_func(f"Setting to ERROR state")
      self.loaderState = TVFileLoaderState.ERROR
      return

    # if we're here, we found at least one colon
    # the preceding string becomes the tag
    self.currentTag = line[0:colonLoc]

    # the following string becomes the value, though we need to check
    # for <text> tags
    line_remainder = line[colonLoc+1:].strip()
    startTagLoc = line_remainder.find("<text>")
    if startTagLoc == -1:
      # no <text> tag, so just grab the value
      self.currentValue = line_remainder
    else:
      # there's a <text> tag; is this multi-line or just one line?
      # skip past <text> tag and check for a closing tag
      line_remainder = line_remainder[startTagLoc+6:]
      endTagLoc = line_remainder.find("</text>")
      if endTagLoc == -1:
        # there's no closing tag, so begin multi-line
        self.currentValue = line_remainder + "\n"
        self.loaderState = TVFileLoaderState.MIDTEXT
        return
      else:
        # found a closing </text> tag, so grab the value
        self.currentValue = line_remainder[:endTagLoc]

    # if we get here, we finished the tag/value pair in this line
    # so go ahead and record it
    t = (self.currentTag, self.currentValue)
    self.tvList.append(t)
    # clean up and proceed
    self._parseResetTagValue()
    self.loaderState = TVFileLoaderState.READY

  ########## PARSER HELPER FUNCTIONS ##########
  def parseNextLine(self, line):
    self.currentLineNum += 1
    # if we've already hit an unrecoverable error, just bail
    if self.loaderState == TVFileLoaderState.ERROR:
      return
    elif self.loaderState == TVFileLoaderState.MIDTEXT:
      self._parseNextLineFromMidtext(line)
    elif self.loaderState == TVFileLoaderState.READY:
      self._parseNextLineFromReady(line)
    else:
      # in some unknown state; switch to error
      # FIXME throw some sort of exception here instead?
      self.log_func(f"Error: line {self.currentLineNum}, unknown loader state: {self.loaderState}")
      self.log_func(f"Setting to ERROR state")
      self.loaderState = TVFileLoaderState.ERROR

  def isError(self):
    return self.loaderState == TVFileLoaderState.ERROR

  def getFinalTVList(self):
    # should be called when the outer program thinks parsing is over.
    # did we end up in a READY state?
    if self.loaderState == TVFileLoaderState.READY:
      return self.tvList
    elif self.loaderState == TVFileLoaderState.ERROR:
      self.log_func("Error: Requested final tag/value list but loader is in ERROR state")
      return None
    elif self.loaderState == TVFileLoaderState.MIDTEXT:
      self.log_func("Error: Requested final tag/value list but loader is still parsing unclosed <text> value")
      self.log_func(f"Setting to ERROR state")
      self.loaderState = TVFileLoaderState.ERROR
      return None
