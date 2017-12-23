#!/usr/bin/python3
#
# drop-abandoned-patches.py - nuke dead patches from RPM trees
#
# Copyright 2016-2017 Intel Corporation
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

import sys
import os
import glob
import subprocess


def emit_error(er):
    """ Emit error to stderr and exit immediately """
    sys.stderr.write(er)
    sys.stderr.flush()
    sys.exit(1)


def consume_spec(spec_file):
    """ Parse the spec file """
    sources = set()
    patches = set()

    with open(spec_file, "r", encoding="latin-1") as inp_file:
        for line in inp_file.readlines():
            line = line.replace("\r", "").replace("\n", "").strip()
            if line == "":
                continue
            splits = line.split(":")
            # Skip URL sources too
            if len(splits) != 2:
                continue
            key = splits[0].strip().lower()
            value = splits[1].strip()
            # Make #commented patches appear "used"
            if key.startswith("#"):
                key = key[1:].strip()
            if key.startswith("patch"):
                patches.add(value)
            elif key.startswith("source"):
                sources.add(value)
    return sources, patches


def main():
    if len(sys.argv) != 2:
        emit_error("usage: {} pkg.spec".format(sys.argv[0]))
    spec_file = sys.argv[1]
    if not os.path.exists(spec_file):
        emit_error("{} doesn't exist - aborting".format(spec_file))
    if not spec_file.endswith(".spec"):
        emit_error("{} doesn't look like a valid spec file".format(spec_file))

    spec_file = os.path.abspath(spec_file)

    # All ops are relative to base_dir
    base_dir = os.path.dirname(spec_file)

    patch_files = set()

    # find all .patch & .diff files
    try:
        searches = ["*.patch", "*.nopatch", "*.diff"]
        for item in searches:
            gl = glob.glob("{}/{}".format(base_dir, item))
            patch_files.update([os.path.basename(x) for x in gl])
    except Exception as e:
        emit_error(e)

    # Parse the .spec file
    sources, patches = consume_spec(spec_file)
    fileset = set()
    fileset.update(sources)
    fileset.update(patches)

    # Find out anything that's unused
    unused = [x for x in patch_files if x not in fileset]
    if len(unused) == 0:
        print("No unused patches")
        sys.exit(0)
    # git rm all the unused patches
    for unused_patch in unused:
        cmd = "git -C \"{}\" rm \"{}\"".format(base_dir, unused_patch)
        try:
            subprocess.check_call(cmd, shell=True)
        except Exception as e:
            emit_error("Cannot remove file {}: {}".format(unused_patch, e))
    # Now commit the changes
    try:
        commit_msg = "Drop unused patches from tree"
        cmd = "git -C \"{}\" commit -m '{}'".format(base_dir, commit_msg)
        subprocess.check_call(cmd, shell=True)
    except Exception as e:
        emit_error("Cannot commit changes: {}".format(e))

if __name__ == '__main__':
    main()
