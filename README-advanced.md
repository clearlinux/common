## Advanced topics

### Manual setup

If you did not run the user-setup script (see "Automated setup" section in the
[main README](README.md), you will want to set up the developer tooling
workspace manually. This section provides general documentation for the manual
setup process, and it is not meant to be exhaustive.

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
