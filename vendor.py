#!/usr/bin/env python3

import argparse
import configparser
import os
import re
import shutil
import subprocess
import tempfile
import time

from git import Repo

import requests


def vendor_check():
    if not os.path.isfile('options.conf'):
        return False
    config = configparser.ConfigParser(interpolation=None)
    config.read('options.conf')
    if 'autospec' not in config.sections():
        return False
    if vendor := config['autospec'].get('cargo_vendor'):
        if vendor == "true":
            return 'cargo'

    return False


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('name')
    parser.add_argument('git')
    return parser.parse_args()


def setup_content(url):
    tdir = tempfile.mkdtemp()
    outfile = os.path.join(tdir, os.path.basename(url))
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    with open(outfile, 'wb') as cfile:
        cfile.write(response.content)

    subprocess.run(f"tar xf {outfile}", shell=True, cwd=tdir, check=True)
    os.remove(outfile)
    return tdir


def setup_cargo_vendor(path):
    for dirpath, _, files in os.walk(path):
        for fname in files:
            if fname == "Cargo.toml":
                return dirpath
    return False


def update_cargo_vendor(path, name, git):
    git_uri = os.path.join(git, name)
    vendor_path = os.path.join(path, 'vendor')
    subprocess.run(f"git clone {git_uri} {vendor_path}", shell=True, check=True)
    vendor_git = os.path.join(vendor_path, '.git')
    if not os.path.isdir(vendor_git):
        # initialize a git repo
        subprocess.run('git init .', cwd=vendor_path, shell=True, check=True)
        subprocess.run(f"git remote add origin {git_uri}", cwd=vendor_path,
                       shell=True, check=True)
    backup_vendor_git = os.path.join(path, 'clear-linux-vendor-git')
    subprocess.run(f"cp -a {vendor_git} {backup_vendor_git}", cwd=path,
                   shell=True, check=True)
    shutil.rmtree(vendor_path)
    subprocess.run('cargo vendor', cwd=path, shell=True, check=True)
    subprocess.run(f"cp -a {backup_vendor_git} {vendor_git}", cwd=path,
                   shell=True, check=True)
    repo = Repo(vendor_path)
    if not (len(repo.untracked_files) > 0 or repo.is_dirty()):
        return False
    subprocess.run('git add .', cwd=vendor_path, shell=True, check=True)
    subprocess.run('git commit -m "vendor update"', cwd=vendor_path,
                   shell=True, check=True)
    gmt = time.gmtime()
    tag = f"{gmt.tm_year}-{gmt.tm_mon:02d}-{gmt.tm_mday:02d}-{gmt.tm_hour:02d}-{gmt.tm_min:02d}-{gmt.tm_sec:02d}"
    subprocess.run(f"git tag {tag}", cwd=vendor_path, shell=True,
                   check=True)
    subprocess.run(f"git push origin main:main {tag}", cwd=vendor_path,
                   shell=True, check=True)
    time.sleep(30)
    return tag


def update_cargo_sources(name, tag):
    makefile = []
    archive_match = os.path.join('$(CGIT_BASE_URL)', 'vendor', name,
                                 'snapshot', name)
    with open('Makefile', encoding='utf8') as mfile:
        for line in mfile.readlines():
            if line.startswith('ARCHIVES'):
                if re.match(archive_match + '[a-zA-Z0-9_\-.]+\.tar\.xz', line):
                    new_archives = re.sub(archive_match + '[a-zA-Z0-9_\-.]+\.tar\.xz',
                                          f"{archive_match}-{tag}.tar.xz\n", line)
                else:
                    new_archives = f"ARCHIVES = {archive_match}-{tag}.tar.xz ./vendor\n"
                makefile.append(new_archives)
            else:
                makefile.append(line)
    with open('Makefile', 'w', encoding='utf8') as mfile:
        mfile.writelines(makefile)


def main():
    vtype = vendor_check()
    if not vtype:
        return

    args = get_args()
    tdir = setup_content(args.url)
    if vtype == 'cargo':
        vdir = setup_cargo_vendor(tdir)
        if vdir:
            tag = update_cargo_vendor(vdir, args.name, args.git)
            if tag:
                update_cargo_sources(args.name, tag)
    shutil.rmtree(tdir)

if __name__ == '__main__':
    main()
