# LTS package maintenance utility

This tooling is designed to automate 2 main tasks that are part of
the package maintenance workflow of Clear Linux LTS. These tasks are:
- Back-porting of a patch (e.g. security fix) to older branches.
- Building RPMs with the intent of sharing binaries of older LTS branches to
  newer branches whenever possible.

There should be no need to run this tool directly. Instead use the following
targets defined in Makefile.common.lts:
- lts-show: Show a summary of active LTS branches
- lts-backport: Attempt to fast-forward the previous active branch to the current branch
- lts-build: Build RPM in Koji, or reuse existing build from older branch

"Active" branches correspond to LTS releases that currently have support.
They are listed in a flat file "active-branches" in "lts" directory, from
oldest to newest. New entries are added by Clear Linux LTS developers as
new releases become available, and entries removed as releases become
obsolete.
