# Copyright (C) 2019  CERN for the benefit of the LHCb collaboration
# Author: Paul Seyfert <pseyfert@cern.ch>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization
# or submit itself to any jurisdiction.

import os
from subprocess import check_output, CalledProcessError
import glob
import stat
import time


def getdb(filename, logger=None):
    try:
        outpath = check_output(
            ["git", "rev-parse", "--git-dir"], cwd=os.path.dirname(filename)
        )
        try:
            common = os.path.commonpath([outpath, filename.encode("utf-8")])
        except AttributeError:
            common = os.path.commonprefix([outpath, filename.encode("utf-8")])
            if not os.path.isdir(common):
                common = os.path.dirname(common)
        if logger is not None:
            logger.debug("git repository root at: {}".format(common))
        ccs = {
            os.stat(f)[stat.ST_MTIME]: f
            for f in glob.glob(os.path.join(
                common,
                b"build.*",
                b"compile_commands.json"))
        }
        if logger is not None:
            logger.debug("found compile_commands.json at: {}".format(ccs))
        lhcbdb = ccs[max(ccs)]
        if logger is not None:
            logger.debug("newest: {} from {}".format(lhcbdb, time.ctime(max(ccs))))
    except (CalledProcessError, ValueError):
        try:
            return None, common
        except NameError:
            return None, None

    return lhcbdb, common
