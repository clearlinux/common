# Developer tooling framework for Clear Linux

This repository includes scripts, configuration files, and makefiles that
enable Clear Linux developers to manage, maintain, and validate changes to
distro packages and projects that are maintained in git repositories.
Development workflows are makefile-driven, and there is a particular focus on
building Clear Linux packages.

## Getting started

### First steps

* Boot a Clear Linux system.
* As the root user, install the `os-clr-on-clr` bundle:

```
# swupd bundle-add os-clr-on-clr
```

### Automated setup

Download the [user setup](user-setup.sh) script and run it on your Clear Linux
system as an unprivileged user.

```
$ curl -O https://raw.githubusercontent.com/clearlinux/common/master/user-setup.sh
$ chmod +x user-setup.sh
$ ./user-setup.sh
```

After the script completes, make sure to logout and login again to complete the
setup process.

The script either accepts no options, or all (3) options in case you are
configuring the Koji CLI for remote building on a Koji server. The options are
documented in the script's `--help` output.

### Manual setup

On your Clear Linux system, create a workspace for Clear Linux development
work:

```
$ mkdir clearlinux
```

Clone this repo into a `projects` directory within the workspace:

```
$ cd clearlinux
$ mkdir projects
$ git clone https://github.com/clearlinux/common projects/common
```

Create the toplevel tooling Makefile:

```
$ ln -s projects/common/Makefile.toplevel Makefile
```

Clone all Clear Linux package and project repositories:

```
$ make clone
```

Note: You can clone the repos in parallel by using make's `-j` option.

At this point, the `packages` directory will contain all Clear Linux package
repos, and `projects` will contain common, clr-bundles, and autospec repos.

## Example usage

### Build RPMs for a package

In every repo cloned to the `packages` tree, several make commands are
available for managing a given package. For example, you can build source,
binary, and debuginfo RPMs for a package by running `make build`.

To build RPMs for the coreutils package, do the following:

```
$ cd packages/coreutils
$ make build
```

The results of `make build` are stored in the `results` directory within the
repo.

Run `make help` to see other make commands that are available to work with the
package.

### Keep up-to-date with latest changes

Due to the frequent release cadence, you may wish to keep repos in the
workspace up-to-date with the most recent changes. To do so, run `make pull` in
the toplevel directory of the workspace. Assuming your current working
directory is a package repo, do:

```
$ cd ../..
$ make pull
```

A `make pull` will display the diffstat for each project and package repo with
changes since you last updated the workspace.

If new packages were added to the distro since the last update, clone the new
package repos by running `make clone`.

Run `make help` to see other make commands available to run at toplevel.

### Autogenerate a new package

The toplevel makefile provides a `make autospecnew` command that can
automatically generate an RPM package by using the `autospec` tool. You must
define the `URL` and `NAME` variables for the command. `URL` is a URL to the
package's upstream source tarball, and `NAME` is the name of the package you
wish to create.

```
$ make autospecnew URL="..." NAME="example-pkg"
```

Whether or not autospec successfully creates the package, a new package
directory will be created to continue work on it. In the example below, a
missing build dependency is added, and then autospec is re-run.

```
$ cd packages/example-pkg
$ echo missing-build-req >> buildreq_add
$ make autospec
```

### Bump the release number for a package

If you simply need to increment a package's release number and rebuild the
package, a `make bump` command is available for this purpose.

```
$ make bump
$ make build
```
