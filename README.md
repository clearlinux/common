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

The script accepts several options, or no options at all. The options are
documented in the script's `--help` output. Note that if you are supplying any
of the three Koji cert options (`-k`, `-s`, or `-c`), the other two options
must be supplied as well.

If you do not wish to run the user-setup script, see the "Manual setup" section
below for hints about how to initialize the tooling workspace.

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

Please see https://github.com/clearlinux/autospec#common-files for 
documention on buildreq_add and the other files autospec uses during the
build process.

### Bump the release number for a package

If you simply need to increment a package's release number and rebuild the
package, a `make bump` command is available for this purpose.

```
$ make bump
$ make build
```

### Update the release version for a package

If you have an update release version for a package, you can change the url
for the new release in the package/example-pkg/Makefile.  After modifying the
new url, run `make autospec` again to fetch the new package and rebuild.

```
$ make autospec
```

## Other topics

### Customizing the mock config

In the past, the various make commands that call `mock` required a mock config
installed at `/etc/mock/clear.cfg`. However, at present, the commands will
instead use the mock config within this repo (`conf/clear.cfg`).

If you wish to use a custom mock config, you must override the `MOCK_CONF`
variable to specify a different value to pass to mock's `-r` option. The value
is either a full path that ends with `.cfg`, or a config NAME installed at
`/etc/mock/<NAME>.cfg`. You can override the `MOCK_CONF` config variable by
redefining it in `Makefile.config.site_local`, which must reside at the
toplevel directory in this repo.

For example, to retain the old behavior of mock using `/etc/mock/clear.cfg`,
add this line to `Makefile.config.site_local`:

```
MOCK_CONF = /etc/mock/clear.cfg
```

If `Makefile.config.site_local` doesn't exist already, create it.

### Manual setup

See the [Manual setup](README-advanced.md#manual-setup) documentation.
