#!/usr/bin/env python3
#
# gowrap.py - part of autospec
# Copyright (C) 2019 Intel Corporation
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

import argparse
import os
import shutil
import subprocess
import sys
import tempfile


def parse_args():
    """Parse commandline arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Location of package archive")
    parser.add_argument("-t", "--target", dest="target", action="store",
                        default=None,
                        help="Target location to create or reuse")
    parser.add_argument("-c", "--config", dest="config", action="store",
                        default="/usr/share/defaults/autospec/autospec.conf",
                        help="Set configuration file to use")
    parser.add_argument("-n", "--name", action="store", dest="name", default="",
                        help="Override the package name")
    parser.add_argument("-i", "--integrity", action="store_true",
                        default=False,
                        help="Search for package signature from source URL and "
                             "attempt to verify package")
    parser.add_argument("-m", "--mock-config", action="store", default="clear",
                        help="Value to pass with Mock's -r option. Defaults to "
                             "\"clear\", meaning that Mock will use "
                             "/etc/mock/clear.cfg.")
    parser.add_argument("-o", "--mock-opts", action="store", default="",
                        help="Arbitrary options to pass down to mock when "
                        "building a package.")
    parser.add_argument('-a', "--archives", action="store",
                        dest="archives", default=[], nargs='*',
                        help="tarball URLs for additional source archives and"
                        " a location for the sources to be extacted to (e.g."
                        " http://example.com/downloads/dependency.tar.gz"
                        " /directory/relative/to/extract/root )")

    return parser.parse_args()


def missing_dependencies(name):
    """Check if the build failed due to missing dependencies."""
    root_log = os.path.join("packages", name, "results", "root.log")
    if not os.path.exists(root_log):
        return False
    with open(root_log, "r") as lfile:
        for line in lfile.readlines():
            if "No matching package to install" in line:
                return True
    return False


def already_built(name, version):
    """Check if the package and version are already built."""
    if not os.path.exists(os.path.join("packages", name, "rpms")):
        return False
    vpath = os.path.join("packages", name, "versions")
    if not os.path.exists(vpath):
        return False
    with open(vpath, "r") as vfile:
            if version not in [x.strip() for x in vfile.readlines()]:
                return False
    return True


def build(path, args, name, url, version):
    """Try and build a package."""
    if version:
        ver_arg = ["-v", version]
    else:
        ver_arg = []
    if already_built(name, version):
        return True
    print(f"Trying to autospec {name} - {version}")

    proc = subprocess.run(["python3",
                           f"{path}/../autospec/autospec/autospec.py", url,
                           "-c", args.config, "-t", f"packages/{name}",
                           "-n", name, "-m", args.mock_config,
                           "-o", args.mock_opts, "-i"] + ver_arg, capture_output=True)
    if proc.returncode == 0:
        subprocess.run(["make", "link-new-rpms", f"PKG_REPO_DIR=packages/{name}"],
                       capture_output=True)
    return proc.returncode == 0


def parse_go_mod(path):
    """Parse go.mod file for build requirements.

    File content looks as follows:

    module example.com/foo/bar

    require (
        github.com/BurntSushi/toml v0.3.1
        git.apache.org/thrift.git v0.0.0-20180902110319-2566ecd5d999
        github.com/inconshreveable/mousetrap v1.0.0 // indirect
        "github.com/spf13/cobra" v0.0.3
        github.com/spf13/pflag v1.0.3 // indirect
    )

    Need to handle all require lines including //indirect.
    Skip requires that use .git for now. May need to be handled
    differently.
    """
    reqs = []
    with open(path, "r") as gfile:
        dep_start = False
        for line in gfile.readlines():
            # Ideally the mod file is generated and the format is
            # always correct but add a few defenses just in case
            line = line.strip()
            if line.startswith("//"):
                # Skip comments
                continue
            if dep_start:
                # End of the require section
                if line.startswith(")"):
                    break
                req = line.split()[:2]
                req[0] = req[0].replace('"', '')
                if req[0].endswith(".git"):
                    continue
                reqs.append(req)
                continue
            if line.startswith("require ("):
                dep_start = True
    return reqs


def get_dependencies(name):
    """Return path to the go.mod file if it exists."""
    command = None
    path = None
    pdir = os.path.join("packages", name)
    reqs = []
    for fname in os.listdir(pdir):
        # Find the archive
        if fname.endswith("zip"):
            command = ["unzip", fname]
        elif ".tar." in fname:
            command = ["tar", "xf", fname]
        else:
            command = None

        if command:
            # Decompress archive
            tdir = tempfile.mkdtemp()
            tfile = os.path.join(tdir, fname)
            shutil.copyfile(os.path.join(pdir, fname), tfile)
            proc = subprocess.run(command, cwd=tdir, capture_output=True)
            if not proc.returncode:
                # inspect contents for a "go.sum" file
                for root, _, files in os.walk(tdir):
                    if "go.mod" in files:
                        path = f"{name}.gomod"
                        shutil.copyfile(os.path.join(root, "go.mod"), path)
                        reqs += parse_go_mod(path)
                        os.unlink(path)
            shutil.rmtree(tdir)

    return reqs


def encode_requirements(requirement):
    """Encode the project's module and version."""
    # Default dependency base proxy url
    base_url = "https://proxy.golang.org/"
    # Encoding based on
    # https://tip.golang.org/cmd/go/#hdr-Module_proxy_protocol
    encoded_module = ""
    for char in requirement[0]:
        if char.isupper():
            encoded_module += "!" + char.lower()
        else:
            encoded_module += char
    encoded_version = ""
    for char in requirement[1]:
        if char.isupper():
            encoded_version += "!" + char.lower()
        else:
            encoded_version += char
    return (encoded_module, encoded_version)


def initialize_package(name, url, version, path, args):
    """Setup package and try to build it."""
    if already_built(name, version):
        return True
    print(f"Trying to autospecnew {name} - {version}")

    proc = subprocess.run(["make", "autospecnew", f"URL={url}", f"NAME={name}", f"SETVERSION={version}"], capture_output=True)
    if f"{name} already exists at" in proc.stdout.decode("utf-8"):
        return build(path, args, name, url, version)
    return proc.returncode == 0


def build_recursive(path, args, name, url, version=None, success=None):
    """Try and recursively build packages."""
    if not success:
        # First package being built, common utilities already run
        # so just use autospec directly
        success = {}
        ret = build(path, args, name, url, version)
    else:
        ret = initialize_package(name, url, version, path, args)

    if ret:
        # Completed so we are done!
        return True

    if not missing_dependencies(name):
        # Failed but not due to missing dependencies, bail
        print(f"Unknown error building {name} - {version}")
        return False

    reqs = get_dependencies(name)
    if not reqs:
        # Didn't try and add anything so don't need to build again
        print(f"Build failed with no missing requirements: {name} - {version}")
        return False

    print(f"First attempt to build failed due to missing dependencies {name} - {version}\n")
    for req in reqs:
        ereq = encode_requirements(req)
        rname = "go-" + req[0].replace("/", "-")
        rurl = f"https://proxy.golang.org/{ereq[0]}/@v/list"
        if (rname, req[1]) in success:
            # Rebuild detected, figure out if it is okay or not
            if success[(rname, req[1])]:
                # Already succeeded building req short circuit success
                continue
            else:
                # Encountered a build loop, bail out as this likely
                # requires manual fixing
                print(f"Detected build loop when building {rname} - {req[1]}")
                return True
        success[(rname, req[1])] = False
        if not build_recursive(path, args, rname, rurl, req[1], success):
            print(f"Failed to build dependency {rname} - {req[1]}")
            return False

        success[(rname, req[1])] = True
        subprocess.run(["make", "repodel"], cwd=f"packages/{rname}", capture_output=True)
        subprocess.run(["make", "repostage"], cwd=f"packages/{rname}", capture_output=True)

    # Create the repo with the new packages added
    subprocess.run(["make", "localrepocreate"], capture_output=True)
    # Retry previously failed build assuming dependencies got added
    print(f"Rebuilding after resolving dependencies {name} - {version}")
    ret = build(path, args, name, url, version)
    print("")

    return ret


def main():
    """Start program execution."""
    args = parse_args()
    path = os.path.dirname(os.path.realpath(__file__))
    return build_recursive(path, args, args.name, args.url)

if __name__ == '__main__':
    if not main():
        sys.exit(-1)
    print("\n\nBuild completed\n\n")
