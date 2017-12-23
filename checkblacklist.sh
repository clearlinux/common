#!/bin/bash
# -*- mode: shell-script; indent-tabs-mode: nil; sh-basic-offset: 4; -*-
# ex: ts=8 sw=4 sts=4 et filetype=sh
#

# return code, set to 1 if Banned file found
FOUND=0

# List the filenames in an rpm file
# Do not use 'rpm -qlp' as it requires an initialized rpm database
list_rpm(){
    rpm2cpio "$1" | cpio -it 2>/dev/null
}

check_rpm_file ()
{
    # BF is the output of this pipeline, the 'if' tests the return
    # status of the pipeline, i.e. the grep.
    if BF=$(list_rpm "$1" |
                sed 's:^\./:/:' |
                grep -Fxf "$BKL"
         )
    then
        for f in $BF ; do
            echo "**************"
            echo "ERROR: Banned file found."
            echo "$f -->  $1"
            echo "**************"
        done >&2
        FOUND=1
    fi
}

####################  main  ####################

# Blacklist as first parameter, rpm files to check as rest
BKL=$1
shift

if ! [ -r "$BKL" ] ; then
    printf "Blacklist file '%q' is not readable!\\n" "$BKL" >&2
    exit 2
fi

for f
do
    check_rpm_file "$f"
done
exit $FOUND

# Testing
#
# Empty blacklist file
# Blacklist file with 1 line, which does match
# Blacklist file with 1 line, which does doesn't match
# Blacklist file with multiple lines, which does match
# Blacklist file with multiple lines, with one match
# Blacklist file with multiple lines, with multiple matches
#
# Check return codes
