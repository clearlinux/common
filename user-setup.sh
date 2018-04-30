#!/bin/bash

SCRIPT=$(/usr/bin/basename $0)
PEM=""
SERVERCA=""
CLIENTCA=""

help() {
	printf "%s\n" >&2 "Usage: $SCRIPT [options]" \
			  "" \
			  "Options:" \
			  "-k --client-cert PEM_FILE: Enable client user cert for koji configuration; requires a PEM file argument" \
			  "-s --server-ca PEM_FILE: Enable server CA cert for koji configuration; requires a PEM file argument" \
			  "-c --client-ca PEM_FILE: Enable client CA cert for koji configuration; requires a PEM file argument" \
			  ""
}

while [ $# -gt 0 ]; do
	case "$1" in
		"--help"|"-h")
			help
			exit 0
			;;
		"--client-cert"|"-k")
			shift
			PEM="$PWD/$1"
			;;
		"--server-ca"|"-s")
			shift
			SERVERCA="$PWD/$1"
			;;
		"--client-ca"|"-c")
			shift
			CLIENTCA="$PWD/$1"
			;;
		*)
			help
			exit 1
			;;
	esac
	shift
done

error() {
	echo -e "Error: $1\n" >&2
	help
	exit 1
}

if [ -z "$PEM" ] && [ -z "$SERVERCA" ] && [ -z "$CLIENTCA" ]; then
	USE_KOJI=
else
	if [ -z "$PEM" ] || [ -z "$SERVERCA" ] || [ -z "$CLIENTCA" ]; then
		error "Must specify all three command line options (or none)"
	fi
	if [ ! -f "$PEM" ]; then
		error "Missing koji client PEM key file"
	fi
	if [ ! -f "$SERVERCA" ]; then
		error "Missing koji server CA PEM file"
	fi
	if [ ! -f "$CLIENTCA" ]; then
		error "Missing koji client CA PEM file"
	fi
	USE_KOJI="yes"
fi

required_progs() {
	local bindir="/usr/bin"
	for f in git mock rpm rpmbuild ; do
		[ ! -x "${bindir}/${f}" ] && missing+="${f} "
	done
	[ "$PEM" ] && [ ! -x /usr/bin/koji ] && missing+="koji "
	if [ -n "$missing" ]; then
		echo "Install the following programs and re-run this script:" >&2
		echo $missing >&2
		echo 'All programs should be provided in the "os-clr-on-clr" bundle.' >&2
		exit 1
	fi
}

required_progs

echo 'Initializing development workspace in "clearlinux" . . .'
if [ -d "clearlinux" ]; then
	echo 'Directory "clearlinux" already exists in current directory.' >&2
	echo "Cannot initialize workspace." >&2
	exit 1
fi

mkdir clearlinux
cd clearlinux

echo "Setting up common repo . . ."
mkdir projects
git clone https://github.com/clearlinux/common projects/common
if [ $? -ne 0 ]; then
	echo "Failed to clone common repo." >&2
	exit 1
fi

# Finish setup for packages/projects hierarchy
ln -sf projects/common/Makefile.toplevel Makefile
mkdir -p packages/common
ln -sf ../../projects/common/Makefile.common packages/common/Makefile.common

if [ "$USE_KOJI" ]; then
	echo "Setting up koji certs . . ."
	mkdir -p ~/.koji
	cp "$PEM" ~/.koji/client.crt
	cp "$CLIENTCA" ~/.koji/clientca.crt
	cp "$SERVERCA" ~/.koji/serverca.crt

	if [ ! -f /etc/koji.conf ]; then
		echo "Setting up koji config . . ."
		sudo cp projects/common/koji-client-files/koji.conf /etc
	fi
fi

if [ ! -f /etc/mock/clear.cfg ]; then
	echo "Setting up mock config . . ."
	sudo mkdir -p /etc/mock
	sudo cp projects/common/koji-client-files/clear.cfg /etc/mock
fi

echo "Adding user to kvm group . . ."
sudo usermod -a -G kvm $USER

echo "Cloning special project repositories . . ."
make clone-projects

if [ -z "$NO_PACKAGE_REPOS" ]; then
	echo "Cloning all package repositories . . ."
	make clone-packages
fi

if [ "$USE_KOJI" ]; then
	echo "Testing koji installation . . ."
	if koji moshimoshi; then
		echo -en "\n************************\n\n"
		echo "Koji installed and configured successfully"
	else
		echo -en "\n************************\n\n"
		echo "Error with koji installation or configuration" >&2
		exit 1
	fi
fi

echo -en "\n************************\n"

echo 'Workspace has been set up in the "clearlinux" directory'
echo 'NOTE: logout and log back in to finalize the setup process'
