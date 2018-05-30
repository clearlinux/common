# Configuration files

This directory contains various configuration files used by the developer
tooling framework.

Unless otherwise noted in the config file documentation below, the config files
can be modified with custom, site-local changes by modifying a variable in
`Makefile.config.site_local` to point to a location of your choice (e.g.
somewhere in `/etc`). The framework will then read the config file from the
location you have specified instead, so copy the in-tree copy to that location
as a starting point if you need to.

* `autospec.conf`: default Autospec configuration file used by `make autospec`
  and `make autospecnew`. All configuration is commented out by default, so
  default Autospec settings are used. Config variable: `AUTOSPEC_CONF`

* `clear.cfg`: default Mock configuration file used by various targets that
  call out to Mock. Config variable: `MOCK_CONF`

* `dnf.conf`: DNF conf for use as the package manager configuration file, made
  available for the framework's local repo support. Config variable: `PM_CONF`

* `yum.conf`: YUM conf for use as the package manager configuration file, made
  available for the framework's local repo support. Config variable: `PM_CONF`

* `koji.conf`: template Koji configuration file. It is installed by
  `user-setup.sh` to `/etc/koji.conf`, and the in-tree copy is not used. If you
  are using Koji with the framework, you will need to modify `/etc/koji.conf`
  according to how the Koji instance is set up for your environment. Configuring
  the installation location via `Makefile.config.site_local` is not possible at
  the moment but is a planned feature.
