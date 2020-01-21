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
import logging
import ycm_core

import imp

# https://stackoverflow.com/a/6683301
lhcb = imp.load_source('lhcb', os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ycm_conf_utils', 'lhcb.py'))
# TODO port to importlib
# https://stackoverflow.com/questions/19009932/import-arbitrary-python-source-file-python-3-3
# import importlib

logger = logging.getLogger("conf_logger")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("/tmp/ycmconflog.log")
logger.addHandler(fh)

# ycm conf is not used from vim directly!
# import vim

def default_flags():
    flags = ["-Wall", "-Werror", "-std=c++17", "-x", "c++", "-DYCM_DIAGS=1"]
    homeinclude = os.path.join(os.environ["HOME"], ".local/include")
    if os.path.isdir(homeinclude):
        flags += ["-I" + homeinclude]
    return flags


def add_root(flags):
    try:
        rootsys = os.environ["ROOTSYS"]
        if os.path.isdir(os.path.join(rootsys, "include")):
            flags += ["-I" + os.path.join(rootsys, "include")]
    except KeyError:
        pass
    return flags


def add_cppflags(flags):
    try:
        envflags = os.environ["CPPFLAGS"].split(" ")
        logger.info("envflags: {}".format(envflags))
        for envflag in envflags:
            logger.debug("checking: {}".format(envflag))
            if envflag.startswith("-I"):
                logger.debug("adding: {}".format(envflag))
                flags += [envflag]
    except KeyError:
        pass
    return flags


def handleDB(dbpath, filename, refdir=None):
    compilation_info = GetCompilationInfoForFile(dbpath, filename)

    if not compilation_info:
        logger.debug("trying generic handling")
        flags = GenericDB(dbpath, refdir)
        logger.debug("before absolution: {}".format(flags))
        final_flags = MakeRelativePathsInFlagsAbsolute(flags, dbpath)
        logger.debug("after absolution:  {}".format(final_flags))
    else:
        final_flags = MakeRelativePathsInFlagsAbsolute(
            compilation_info.compiler_flags_,
            compilation_info.compiler_working_dir_
        )

    return final_flags


SOURCE_EXTENSIONS = [".cpp", ".cxx", ".cc", ".c", ".m", ".mm"]
HEADER_EXTENSIONS = [".h", ".hxx", ".hpp", ".hh"]


def IsHeaderFile(filename):
    if os.path.splitext(filename)[-1] in HEADER_EXTENSIONS:
        return True
    # consider something.h.cpp
    if os.path.splitext(filename)[-1] in SOURCE_EXTENSIONS:
        return False
    # consider something.cpp.orig
    if os.path.splitext(filename)[1] in HEADER_EXTENSIONS:
        return True
    if os.path.splitext(filename)[1] in SOURCE_EXTENSIONS:
        return False
    return False


def GetCompilationInfoForFile(dbpath, filename):
    # The compilation_commands.json file generated by CMake does not have
    # entries for header files. So we do our best by asking the db for flags
    # for a corresponding source file, if any. If one exists, the flags for
    # that file should be good enough.

    logger.debug("parsing db from {}".format(dbpath))
    logger.debug("for file        {}".format(filename))
    try:
        database = ycm_core.CompilationDatabase(dbpath)
    except Exception as e:
        logger.debug("couldn't open db: {}".format(e))
    if IsHeaderFile(filename):
        logger.debug("looks like a header")
        basename = os.path.splitext(filename)[0]
        for extension in SOURCE_EXTENSIONS:
            replacement_file = basename + extension
            if os.path.exists(replacement_file):
                compilation_info = database.GetCompilationInfoForFile(
                    replacement_file)
                if compilation_info.compiler_flags_:
                    return compilation_info
        logger.debug("not found in DB")
        return None
    logger.debug("looks like a source")
    try:
        retval = database.GetCompilationInfoForFile(filename)
    except Exception as e:
        logger.debug("couldn't read from db: {}".format(e))
        return None

    return retval


def GenericDB(dbpath, refdir=None):
    import numpy.ctypeslib as npct
    import ctypes
    libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "src")
    logger.debug("loading go libs from {}".format(libdir))
    try:
        lib = npct.load_library("py_cc2ce", libdir)
    except OSError:
        logger.debug("didn't build the py_cc2ce.so library")
        # FIXME: make a user visible error message
        return None
    fun_o = lib.GETOPTS
    fun_o.restype = ctypes.c_char_p
    fun_o.argtypes = [ctypes.c_char_p]
    retval = fun_o(dbpath)

    fun_i = lib.GETINCS
    fun_i.restype = ctypes.c_char_p
    fun_i.argtypes = [ctypes.c_char_p]
    incdirs = [x for x in fun_i(dbpath).split(b" ")]

    for inc in incdirs:
        if inc == b"":
            continue
        if refdir is None:
            retval += b"-I" + inc + b" "
        else:
            juggel = os.path.relpath(inc, refdir)
            if juggel[0:2] == "..":
                retval += b"-isystem " + inc + b" "
            else:
                retval += b"-I" + inc + b" "

    logger.debug("returning {}".format(retval))
    return retval.split(b" ")


def MakeRelativePathsInFlagsAbsolute(flags, working_directory):
    if flags is None:
        return None
    if not working_directory:
        logger.debug("skipping absolution")
        return list(flags)
    logger.debug("doing absolution")
    new_flags = []
    make_next_absolute = False
    if type(flags[0]) == str:
        logger.debug("dealing with strings")
        path_flags = ["-isystem", "-I", "-iquote", "--sysroot="]
        root = "/"
    else:
        logger.debug("dealing with bytes")
        path_flags = [b"-isystem", b"-I", b"-iquote", b"--sysroot="]
        root = b"/"
    for flag in flags:
        new_flag = flag

        if make_next_absolute:
            make_next_absolute = False
            if not flag.startswith(root):
                new_flag = os.path.join(working_directory, flag)

        for path_flag in path_flags:
            if flag == path_flag:
                make_next_absolute = True
                break

            if flag.startswith(path_flag):
                path = flag[len(path_flag):]
                new_flag = path_flag + os.path.join(working_directory, path)
                break

        if new_flag:
            new_flags.append(new_flag)
    return new_flags


def FlagsForFile(filename):
    lhcbdb, common = lhcb.getdb(filename, logger)
    if lhcbdb is not None:
        flags = handleDB(os.path.dirname(lhcbdb), filename, common)
        # see above, vim not available from ycm conf
        # done now through ftplugin
        # vim.command("let &makeprg=\"ninja -C {}\"".format(os.path.dirname(lhcbdb)))
        logger.debug("flags: {}".format(flags))
    else:
        flags = None
        if common is not None:
            logger.debug("no usable LHCb build dir found")
            testbuild = os.path.join(common, b"build")
            if os.path.isdir(testbuild) and os.path.exists(
                os.path.join(testbuild, b"compile_commands.json")
            ):
                flags = handleDB(testbuild, filename, common)
            else:
                testbuild = os.path.join(os.path.dirname(common), b"build")
                if os.path.isdir(testbuild) and os.path.exists(
                    os.path.join(testbuild, b"compile_commands.json")
                ):
                    flags = handleDB(testbuild, filename, common)
        else:
            logger.debug("not in a git repo")

    if flags is None:
        flags = default_flags()
        flags = add_root(flags)
        flags = add_cppflags(flags)

    #  BODGING until it works ...

    # LXPLUS
    # flags += [b"-nostdinc"]

    # flags += [b"-isystem", b"/cvmfs/lhcb.cern.ch/lib/lcg/releases/gcc/8.2.0/x86_64-centos7/lib/gcc/x86_64-pc-linux-gnu/8.2.0/../../../../include/c++/8.2.0"]
    # flags += [b"-isystem", b"/cvmfs/lhcb.cern.ch/lib/lcg/releases/gcc/8.2.0/x86_64-centos7/lib/gcc/x86_64-pc-linux-gnu/8.2.0/../../../../include/c++/8.2.0/x86_64-pc-linux-gnu"]
    # flags += [b"-isystem", b"/cvmfs/lhcb.cern.ch/lib/lcg/releases/gcc/8.2.0/x86_64-centos7/lib/gcc/x86_64-pc-linux-gnu/8.2.0/../../../../include/c++/8.2.0/backward"]
    # flags += [b"-isystem", b"/usr/local/include"]
    # flags += [b"-isystem", b"/cvmfs/lhcb.cern.ch/lib/lcg/releases/clang/8.0.0/x86_64-centos7/lib/clang/8.0.0/include/"]
    # # flags += [b"-isystem", b"/afs/cern.ch/user/p/pseyfert/.vim/os_dependent_bundle/YouCompleteMe/third_party/ycmd/clang_includes/include"]
    # flags += [b"-isystem", b"/usr/include"]

    # flags += [b"-x", b"c++"]

    # ROBUSTA

    # flags += [b"-isystem", b"/usr/bin/../lib64/gcc/x86_64-pc-linux-gnu/8.3.0/../../../../include/c++/8.3.0"]
    # flags += [b"-isystem", b"/usr/bin/../lib64/gcc/x86_64-pc-linux-gnu/8.3.0/../../../../include/c++/8.3.0/x86_64-pc-linux-gnu"]
    # flags += [b"-isystem", b"/usr/bin/../lib64/gcc/x86_64-pc-linux-gnu/8.3.0/../../../../include/c++/8.3.0/backward"]
    flags += [b"-isystem", b"/usr/bin/../lib64/gcc/x86_64-pc-linux-gnu/9.2.0/../../../../include/c++/9.2.0"]
    flags += [b"-isystem", b"/usr/bin/../lib64/gcc/x86_64-pc-linux-gnu/9.2.0/../../../../include/c++/9.2.0/x86_64-pc-linux-gnu"]
    flags += [b"-isystem", b"/usr/bin/../lib64/gcc/x86_64-pc-linux-gnu/9.2.0/../../../../include/c++/9.2.0/backward"]


    flags += [b"-isystem", b"/usr/local/include"]
    flags += [b"-isystem", b"/usr/share/vim/vimfiles/third_party/ycmd/third_party/clang/lib/clang/9.0.0/include"]
    flags += [b"-isystem", b"/usr/include"]

    # flags += [b"-resource-dir=/usr/share/vim/vimfiles/third_party/ycmd/third_party/clang/lib/clang/8.0.0"]

    # DONE
    return {"flags": flags, "do_cache": True}
