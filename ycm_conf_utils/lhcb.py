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
try:
    from subprocess import check_output, CalledProcessError
except ImportError:
    # This section section taken from pep8radius
    # Copyright (c) [2014] [Andy Hayden]
    #
    # Permission is hereby granted, free of charge, to any person obtaining a copy of
    # this software and associated documentation files (the "Software"), to deal in
    # the Software without restriction, including without limitation the rights to
    # use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
    # the Software, and to permit persons to whom the Software is furnished to do so,
    # subject to the following conditions:
    #
    # The above copyright notice and this permission notice shall be included in all
    # copies or substantial portions of the Software.
    #
    # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
    # FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
    # COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
    # IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
    # CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

    try:
        from subprocess import STDOUT, check_output, CalledProcessError
    except ImportError:  # pragma: no cover
        # python 2.6 doesn't include check_output
        # monkey patch it in!
        import subprocess
        STDOUT = subprocess.STDOUT

        def check_output(*popenargs, **kwargs):
            if 'stdout' in kwargs:  # pragma: no cover
                raise ValueError('stdout argument not allowed, '
                                 'it will be overridden.')
            process = subprocess.Popen(stdout=subprocess.PIPE,
                                       *popenargs, **kwargs)
            output, _ = process.communicate()
            retcode = process.poll()
            if retcode:
                cmd = kwargs.get("args")
                if cmd is None:
                    cmd = popenargs[0]
                raise subprocess.CalledProcessError(retcode, cmd,
                                                    output=output)
            return output
        subprocess.check_output = check_output

        # overwrite CalledProcessError due to `output`
        # keyword not being available (in 2.6)
        class CalledProcessError(Exception):

            def __init__(self, returncode, cmd, output=None):
                self.returncode = returncode
                self.cmd = cmd
                self.output = output

            def __str__(self):
                return "Command '%s' returned non-zero exit status %d" % (
                    self.cmd, self.returncode)
        subprocess.CalledProcessError = CalledProcessError

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
            logger.debug("git repository root at: {0}".format(common))
        ccs = {}
        for f in glob.glob(os.path.join(
                common,
                b"build.*",
                b"compile_commands.json")):
            ccs[os.stat(f)[stat.ST_MTIME]] = f
        if logger is not None:
            logger.debug("found compile_commands.json at: {0}".format(ccs))
        # if several compile_commands data bases are found, pick the newest:
        # the dict is key'ed by MTIME.
        lhcbdb = ccs[max(ccs)]
        if logger is not None:
            logger.debug("newest: {0} from {1}".format(
                lhcbdb, time.ctime(max(ccs))))
    except (CalledProcessError, ValueError):
        try:
            return None, common
        except NameError:
            return None, None

    return lhcbdb, common
