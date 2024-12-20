#!/usr/bin/env python3

import argparse
import configparser
import os
import re
import shutil
import subprocess
import tempfile
import time

import requests
from git import Repo


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
    parser.add_argument('archives')
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

    subprocess.run(f"tar xf {outfile}", shell=True, cwd=tdir, check=True, stdout=subprocess.DEVNULL)
    os.remove(outfile)
    return tdir


def setup_cargo_vendor(path):
    cargo_paths = []
    for dirpath, _, files in os.walk(path):
        for fname in files:
            if fname == "Cargo.toml":
                cargo_paths.append(os.path.join(dirpath, fname))
    return cargo_paths


def update_cargo_vendor(tmpdir, cargo_paths, name, git):
    git_uri = os.path.join(git, name)
    vendor_path = os.path.join(tmpdir, 'vendor')
    subprocess.run(f"git clone {git_uri} {vendor_path}", shell=True, check=True,
                   stdout=subprocess.DEVNULL)
    vendor_git = os.path.join(vendor_path, '.git')
    if not os.path.isdir(vendor_git):
        # initialize a git repo
        subprocess.run('git init .', cwd=vendor_path, shell=True, check=True,
                       stdout=subprocess.DEVNULL)
        subprocess.run(f"git remote add origin {git_uri}", cwd=vendor_path,
                       shell=True, check=True, stdout=subprocess.DEVNULL)
    backup_vendor_git = os.path.join(tmpdir, 'clear-linux-vendor-git')
    subprocess.run(f"cp -a {vendor_git} {backup_vendor_git}", cwd=tmpdir,
                   shell=True, check=True, stdout=subprocess.DEVNULL)
    shutil.rmtree(vendor_path)
    vendor_cmd = 'cargo vendor ' + ' '.join([f"-s {x}" for x in cargo_paths[:-1]])
    vendor_cmd += f" --manifest-path {cargo_paths[-1]}"
    cargo_vendors = subprocess.run(vendor_cmd, cwd=tmpdir, shell=True,
                                   check=True, stdout=subprocess.PIPE,
                                   universal_newlines=True).stdout
    with open(os.path.join(vendor_path, ".gitattributes"), "w", encoding='utf8') as gafile:
        gafile.write("* text=false\n")
    subprocess.run(f"cp -a {backup_vendor_git} {vendor_git}", cwd=tmpdir,
                   shell=True, check=True, stdout=subprocess.DEVNULL)
    repo = Repo(vendor_path)
    if not (len(repo.untracked_files) > 0 or repo.is_dirty()):
        # Always use the newest tag as sometimes a new tag will
        # be created but the package won't be updated to use it
        # for a different failure reason.
        tag = sorted(repo.tags, key=lambda x: x.name, reverse=True)[0]
        return tag, cargo_vendors
    subprocess.run('git add .', cwd=vendor_path, shell=True, check=True,
                   stdout=subprocess.DEVNULL)
    subprocess.run('git commit -m "vendor update"', cwd=vendor_path,
                   shell=True, check=True, stdout=subprocess.DEVNULL)
    gmt = time.gmtime()
    tag = f"{gmt.tm_year}-{gmt.tm_mon:02d}-{gmt.tm_mday:02d}-{gmt.tm_hour:02d}-{gmt.tm_min:02d}-{gmt.tm_sec:02d}"
    subprocess.run(f"git tag {tag}", cwd=vendor_path, shell=True,
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(f"git push origin main:main {tag}", cwd=vendor_path,
                   shell=True, check=True, stdout=subprocess.DEVNULL)
    time.sleep(30)
    return tag, cargo_vendors


def update_cargo_sources(name, tag, cargo_vendors):
    makefile = []
    options = []
    archive_match = os.path.join(r'\$\(CGIT_BASE_URL\)', 'vendor', name,
                                 'snapshot', name)
    archive_replace = os.path.join('$(CGIT_BASE_URL)', 'vendor', name,
                                   'snapshot', name)
    with open('Makefile', encoding='utf8') as mfile:
        for line in mfile.readlines():
            if line.startswith('ARCHIVES'):
                if re.search(archive_match + r'[a-zA-Z0-9_\-.]+\.tar\.gz', line):
                    new_archives = re.sub(archive_match + r'[a-zA-Z0-9_\-.]+\.tar\.gz',
                                          f"{archive_replace}-{tag}.tar.gz", line)
                else:
                    new_archives = f"{line[:-1]} {archive_replace}-{tag}.tar.gz ./vendor\n"
                print(new_archives.replace('ARCHIVES = ', '', 1))
                makefile.append(new_archives)
            else:
                makefile.append(line)
    with open('Makefile', 'w', encoding='utf8') as mfile:
        mfile.writelines(makefile)

    archive_match = os.path.join('http://localhost', 'cgit', 'vendor', name,
                                 'snapshot', name)
    with open('options.conf', encoding='utf8') as ofile:
        for line in ofile.readlines():
            if line.startswith('archives'):
                if re.search(archive_match + r'[a-zA-Z0-9_\-.]+\.tar\.gz', line):
                    new_archives = re.sub(archive_match + r'[a-zA-Z0-9_\-.]+\.tar\.gz',
                                          f"{archive_match}-{tag}.tar.gz", line)
                else:
                    new_archives = f"{line[:-1]} {archive_match}-{tag}.tar.gz ./vendor\n"
                options.append(new_archives)
            else:
                options.append(line)
    with open('options.conf', 'w', encoding='utf8') as ofile:
        ofile.writelines(options)
    with open('cargo_vendors', 'w', encoding='utf8') as cfile:
        cfile.write(cargo_vendors)


def main():
    args = get_args()

    vtype = vendor_check()
    if not vtype:
        print(args.archives)
        return

    tdir = setup_content(args.url)
    if vtype == 'cargo':
        cargo_paths = setup_cargo_vendor(tdir)
        if len(cargo_paths) == 0:
            print(args.archives)
        else:
            tag, cargo_vendors = update_cargo_vendor(tdir, cargo_paths, args.name, args.git)
            update_cargo_sources(args.name, tag, cargo_vendors)
    shutil.rmtree(tdir)


if __name__ == '__main__':
    main()
