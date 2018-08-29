
all:

clean:
proper:

install:
	if [ ! -f ../../Makefile ]; then echo "include projects/common/Makefile.toplevel" > ../../Makefile; fi

ifdef CLEAR_VER
BASE_URL := https://cdn.download.clearlinux.org/releases/${CLEAR_VER}/clear
else
BASE_URL := https://cdn.download.clearlinux.org/current
endif

update:
	curl -f -o packages ${BASE_URL}/source/package-sources
	cut -f1 packages | LC_ALL=C sort > packages.new && mv packages.new packages

.PHONY: spdx
spdx:
	JSON=$$(mktemp); \
	trap "rm $$JSON" EXIT; \
	curl -f -S -s https://raw.githubusercontent.com/spdx/license-list-data/master/json/licenses.json > $$JSON || exit 1; \
	jq -r '.licenses[] | .licenseId' < $$JSON | LC_COLLATE=C sort > licenses-spdx
