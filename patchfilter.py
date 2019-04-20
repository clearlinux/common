#!/usr/bin/python3
import sys
import tempfile
import subprocess

header = list()
files = list()
files_chunks = dict()	# dict to list
files_header = dict()	# dict to list



def push_chunk(file, chunk):
    global files_chunks
    
    if len(chunk) == 0:
        return
    
    if file not in files_chunks:
        files_chunks[file] = list()
        
    files_chunks[file].append(chunk)


def parse_patch(lines):
    global header
    global files
    global files_chunks
    global files_header
    
    phase = 0
    
    currentfile = ""
    currentchunk = list()
    
        
    for line in lines:
        line = line.replace("\n","")
        
        if line.startswith("diff --git"):
        
            push_chunk(currentfile, currentchunk)
            currentchunk = list()
        
            filename = line.replace("diff --git","")
            index= filename.find("b/")
            if index >= 0:
                filename = filename[index:].strip()
                currentfile = filename
                files.append(currentfile)
                phase = 1
                
        if line.startswith("@@"):
            push_chunk(currentfile, currentchunk)
            currentchunk = list()
            phase = 2
            
            
        if phase == 0:
            header.append(line)
        if phase == 1:
            if currentfile not in files_header:
                files_header[currentfile] = list()
            files_header[currentfile].append(line) 
        if phase == 2:
            currentchunk.append(line)
        
    push_chunk(currentfile, currentchunk)
    currentchunk = list()

def print_all():
    global header
    global files
    global files_chunks
    global files_header

    for line in header:
        print(line)
    for file in files:
        for line in files_header[file]:
            print(line)
        if file in files_chunks:
            for chunk in files_chunks[file]:
                for line in chunk:
                    print(line)
                    
                    
def zap_entire_file(filename):
    global header
    global files
    global files_chunks
    global files_header
    if filename in files:
        files.remove(filename)                

def zap_entire_file_end(filename):
    global header
    global files
    global files_chunks
    global files_header
    for file in files:
        if file.endswith(filename):
            files.remove(file)                
            
def zap_line_in_file(filename, match):
    global header
    global files
    global files_chunks
    global files_header
    for file in files:
        if file.endswith(filename):
            for chunk in files_chunks[filename]:
                to_delete = list()
                for line in chunk:
                    if line == ("+" + match):
                        to_delete.append(line)
                    if line == ("-" + match):
                        to_delete.append(line)
                for line in to_delete:
                    chunk.remove(line)
            

def zap_line_in_file_start(filename, match):
    global header
    global files
    global files_chunks
    global files_header
    
    for file in files:
        if file.endswith(filename):
            for chunk in files_chunks[file]:
                to_remove = list()
                for line in chunk:
                    if line.startswith("+" + match):
                        to_remove.append(line)
                    if line.startswith("-" + match):
                        to_remove.append(line)
                for line in to_remove:
                    chunk.remove(line)
            
def zap_plus_line_in_file(filename):
    global header
    global files
    global files_chunks
    global files_header
    
    for file in files:
        if file.endswith(filename):
            for chunk in files_chunks[file]:
                to_remove = list()
                for line in chunk:
                    if line.startswith("+"):
                        to_remove.append(line)
                for line in to_remove:
                    chunk.remove(line)
            


def chunk_empty(chunk):
    for line in chunk:
        if line[0] == '+':
            return False
    return True
                           
def zap_empty_chunks():
    global header
    global files
    global files_chunks
    global files_header
    files_to_remove = list()
    for file in files:
        if file not in files_chunks:
            files.remove(file)
            continue
        to_remove = list()
        for chunk in files_chunks[file]:
            if chunk_empty(chunk):
                to_remove.append(chunk)
        for c in to_remove:
            files_chunks[file].remove(c)
        if len(files_chunks[file]) == 0:
            files_to_remove.append(file)
            
    for file in files_to_remove:
        files.remove(file)
            
            


def main():

    if len(sys.argv) > 1:
        filename = sys.argv[1]
    
        with open (filename, "r") as myfile:
            lines = myfile.readlines()
    else:
        output = subprocess.check_output("git show", shell=True).decode("latin-1")
        lines = output.split("\n")
        
    parse_patch(lines)

    zap_entire_file("b/release")
    zap_entire_file("b/buildreq_cache")
    zap_entire_file("b/.gitignore")
    zap_entire_file("b/upstream")
    zap_entire_file("b/NEWS")
    zap_entire_file_end("xz.sig")
    zap_entire_file_end("gz.sig")
    zap_entire_file_end("bz2.sig")
    
    zap_line_in_file("b/testresults", "Total : 0")
    zap_line_in_file("b/testresults", "Pass : 0")
    zap_line_in_file("b/testresults", "Fail : 0")
    zap_line_in_file("b/testresults", "XFail : 0")
    zap_line_in_file("b/testresults", "Skip : 0")
    
    zap_line_in_file("b/requires_ban", "#FOO")
    zap_line_in_file("b/Makefile", "ARCHIVES = ")
    zap_line_in_file("b/Makefile", "include ../common/Makefile.common")
    zap_line_in_file("b/Makefile", "")
    
    zap_line_in_file_start(".spec", "Release  :")
    zap_line_in_file_start(".spec", "Source99 :")
    zap_line_in_file_start(".spec", "Source0  :")
    zap_line_in_file_start(".spec", "export SOURCE_DATE_EPOCH")
    zap_line_in_file_start(".spec", "%setup -q -n ")
    zap_line_in_file_start(".spec", "URL      :")
    zap_line_in_file_start(".spec", "Version  :")
    zap_line_in_file_start(".spec", "Group    : Development/Tools")
    zap_line_in_file_start(".spec", "No detailed description available")
    zap_line_in_file_start(".spec", "bin components for the")
    zap_line_in_file_start(".spec", "dev components for the")
    zap_line_in_file_start(".spec", "lib components for the")
    zap_line_in_file_start(".spec", "data components for the")
    zap_line_in_file_start(".spec", "locales components for the")
    zap_line_in_file_start(".spec", "license components for the")
    zap_line_in_file_start(".spec", "Group: Default")
    zap_line_in_file_start(".spec", "export http_proxy=http://127.0.0.1:9/")
    zap_line_in_file_start(".spec", "export https_proxy=http://127.0.0.1:9/")
    zap_line_in_file_start(".spec", "export ftp_proxy=http://127.0.0.1:9/")
    zap_line_in_file_start(".spec", "export no_proxy=localhost,127.0.0.1,0.0.0.0")
    zap_line_in_file_start(".spec", "Summary:")
    zap_line_in_file_start(".spec", "Group: Development")
    zap_line_in_file_start(".spec", "Group: Binaries")
    zap_line_in_file_start(".spec", "Group: Data")
    zap_line_in_file_start(".spec", "Group: Libraries")
    zap_line_in_file_start(".spec", "export LANG=C")
    zap_line_in_file_start(".spec", "%description lib")
    zap_line_in_file_start(".spec", "%description bin")
    zap_line_in_file_start(".spec", "%description data")
    zap_line_in_file_start(".spec", "%description locales")
    zap_line_in_file_start(".spec", "%description dev")
    zap_line_in_file_start(".spec", "%description license")
 
    zap_line_in_file_start("b/Makefile", "URL =")
    zap_line_in_file_start("b/Makefile", "PKG_NAME :=")

    zap_line_in_file("b/options.conf", "archives = ")
    zap_line_in_file("b/options.conf", "giturl = ")
    zap_line_in_file("b/options.conf", "[package]")
    zap_line_in_file("b/options.conf", "")
    zap_line_in_file("b/options.conf", "[autospec]")
    zap_line_in_file("b/options.conf", "# build 32 bit libraries")
    zap_line_in_file("b/options.conf", "32bit = false")
    zap_line_in_file("b/options.conf", "# allow package to build with test failures")
    zap_line_in_file("b/options.conf", "allow_test_failures = false")
    zap_line_in_file("b/options.conf", "# unset %build ld_as_needed variable")
    zap_line_in_file("b/options.conf", "asneeded = false")
    zap_line_in_file("b/options.conf", "# this package is trusted enough to automatically update (used by other tools)")
    zap_line_in_file("b/options.conf", "autoupdate = false")
    zap_line_in_file("b/options.conf", "# extend flags with '-std=gnu++98")
    zap_line_in_file("b/options.conf", "broken_c++ = false")
    zap_line_in_file("b/options.conf", "# disable parallelization during build")
    zap_line_in_file("b/options.conf", "broken_parallel_build = false")
    zap_line_in_file("b/options.conf", "# this package is a library compatability package and only ships versioned library files")
    zap_line_in_file("b/options.conf", "compat = false")
    zap_line_in_file("b/options.conf", "# set conservative build flags")
    zap_line_in_file("b/options.conf", "conservative_flags = false")
    zap_line_in_file("b/options.conf", "# dev package requires the extras to be installed")
    zap_line_in_file("b/options.conf", "dev_requires_extras = false")
    zap_line_in_file("b/options.conf", "# pass -ffast-math to compiler")
    zap_line_in_file("b/options.conf", "fast-math = false")
    zap_line_in_file("b/options.conf", "# optimize build for speed over size")
    zap_line_in_file("b/options.conf", "funroll-loops = false")
    zap_line_in_file("b/options.conf", "# set flags to smallest -02 flags possible")
    zap_line_in_file("b/options.conf", "insecure_build = false")
    zap_line_in_file("b/options.conf", "# do not remove static libraries")
    zap_line_in_file("b/options.conf", "keepstatic = false")
    zap_line_in_file("b/options.conf", "# do not require autostart subpackage")
    zap_line_in_file("b/options.conf", "no_autostart = false")
    zap_line_in_file("b/options.conf", "# disable stripping binaries")
    zap_line_in_file("b/options.conf", "nostrip = false")
    zap_line_in_file("b/options.conf", "# optimize build for size over speed")
    zap_line_in_file("b/options.conf", "optimize_size = false")
    zap_line_in_file("b/options.conf", "# set profile for pgo")
    zap_line_in_file("b/options.conf", "pgo = false")
    zap_line_in_file("b/options.conf", "# set flags for security-sensitive builds")
    zap_line_in_file("b/options.conf", "security_sensitive = false")
    zap_line_in_file("b/options.conf", "# do not run test suite")
    zap_line_in_file("b/options.conf", "skip_tests = false")
    zap_line_in_file("b/options.conf", "# add .so files to the lib package instead of dev")
    zap_line_in_file("b/options.conf", "so_to_lib = false")
    zap_line_in_file("b/options.conf", "# configure build for avx2")
    zap_line_in_file("b/options.conf", "use_avx2 = false")
    zap_line_in_file("b/options.conf", "# configure build for avx512")
    zap_line_in_file("b/options.conf", "use_avx512 = false")
    zap_line_in_file("b/options.conf", "# add clang flags")
    zap_line_in_file("b/options.conf", "use_clang = false")
    zap_line_in_file("b/options.conf", "# configure build for lto")
    zap_line_in_file("b/options.conf", "use_lto = false")
    zap_line_in_file("b/options.conf", "# require package verification for build")
    zap_line_in_file("b/options.conf", "verify_required = true")

    zap_line_in_file("b/buildreq_add", "# This file contains additional build requirements that did not get")
    zap_line_in_file("b/buildreq_add", "# picked up automatically. One name per line, no whitespace.")
    zap_line_in_file("b/buildreq_ban", "# This file contains build requirements that get picked up but are")
    zap_line_in_file("b/buildreq_ban", "# undesirable. One entry per line, no whitespace.")
    
    
    zap_line_in_file("b/excludes", "# This file contains the output files that need %exclude. Full path")
    zap_line_in_file("b/excludes", "# names, one per line.")

    zap_line_in_file("b/pkgconfig_add", "# This file contains additional pkgconfig build requirements that did")
    zap_line_in_file("b/pkgconfig_add", "# not get picked up automatically. One name per line, no whitespace.")
    zap_line_in_file("b/pkgconfig_ban", "# This file contains pkgconfig build requirements that get picked up")
    zap_line_in_file("b/pkgconfig_ban", "# but are undesirable. One entry per line, no whitespace.")
    zap_line_in_file("b/requires_add", "# This file contains additional runtime requirements that did not get")
    zap_line_in_file("b/requires_add", "# picked up automatically. One name per line, no whitespace.")
    zap_line_in_file("b/requires_ban", "# This file contains runtime requirements that get picked up but are")
    zap_line_in_file("b/requires_ban", "# undesirable. One entry per line, no whitespace.")
    
    zap_line_in_file_start(".spec", "Summary  : No detailed summary available")
    
    zap_plus_line_in_file("symbols")
    zap_plus_line_in_file("symbols32")

    zap_empty_chunks()
    
    print_all()

if __name__ == '__main__':
    with tempfile.TemporaryDirectory() as workingdir:
        main()

