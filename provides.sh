#!/bin/bash

RELEASE=0
FILE_PATH="-r"

show_help() {
  echo "Usage: $0  [OPTIONS]"
  echo
  echo "Search "
  echo
  echo " -f, --file PATH          full file path to search."
  echo
  echo "Optional: "
  echo " -r, --release RELEASE    OS release number. Ex. 18400"
  echo "                          if not specified last release will be used"
  echo
}


if [ "$#" -eq 0 ]; then
  show_help
  exit 0
fi

if [ ! -e /etc/yum.conf ]; then
  echo "Error: yum.conf is missing. Please copy projects/common/image-creator/yum.conf to /etc"
  exit 1
fi

while [ -n "$1" ]; do
  case  "$1" in
    -r | --release)
	shift
        RELEASE=$1
	shift
     ;;
    -f | --file)
	shift
        FILE_PATH=$1
	shift
     ;;
    *)
        echo "$1: Invalid option" 1>&2
	exit 1
     ;;
  esac
done

if [ "${RELEASE}" = "0" -o -z "${RELEASE}" ]; then
  RELEASE=$(curl -s https://download.clearlinux.org/latest)
fi

if [ "${FILE_PATH}" = "-r" ]; then
  show_help
  exit 1
fi

REPO_URL="https://download.clearlinux.org/releases/${RELEASE}/clear/x86_64/os"

repoquery --repoid=${RELEASE} \
	--repofrompath=${RELEASE},${REPO_URL} \
	--whatprovides ${FILE_PATH}
