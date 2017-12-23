
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
	cut -f1 packages | LC_ALL=en_US.utf8 sort > packages.new && mv packages.new packages

spdx:
	curl -s spdx.org/licenses/ | sed '0,/<tbody>/d;/<\/tbody>/q;s/<tr>/\f/g;s/$$/,/g;s/<[^>]*>//g' | awk 'BEGIN{RS="\f";FS=","} {print $$4}' | sed '/^$$/d;s/^[ ]*//' > spdx
