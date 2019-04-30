import pathlib
from subprocess import PIPE, CalledProcessError
from .shell import Shell

class PackageRepo:
    '''Represents a package repository. Most methods are wrappers of git commands.'''
    class UnknownCurrentBranchException(Exception): pass
    class InvalidBranchException(Exception): pass

    def __init__(self, name, path):
        self.name = name
        self.path = pathlib.Path(path)
        self.sh = Shell(self.path)

    def getNVR(self, commit='HEAD'):
        with self.sh.popen(['git', 'show', '{}:{}.spec'.format(commit, self.name)], stdout=PIPE) as specfile:
            nvr = self.sh.run('rpmspec --srpm -q --queryformat %{NVR} /dev/stdin', stdin=specfile.stdout)
        return tuple(nvr.stdout.strip().split('-'))

    def checkoutBranch(self, branch, allow_remote=False):
        # allow_remote=True allows checking out a new remote-tracking branch
        if not allow_remote and not self.hasBranch(branch):
            raise self.InvalidBranchException(branch)
        self.sh.run_args(['git', 'checkout', branch], capture_output=False)

    def fastForwardBranch(self, old, new):
        self.checkoutBranch(old)
        if not self.hasBranch(new):
            raise self.InvalidBranchException(new)
        self.sh.run_args(['git', 'merge', '--ff-only', new], capture_output=False)

    def getActiveBranches(self):
        toplvl = pathlib.Path(self.path) / '../..'
        common = toplvl / 'projects/common'
        active_branches = common / 'lts/active-branches'
        with active_branches.open() as f:
            return [line.rstrip() for line in f]

    def getCurrentBranch(self):
        try:
            head = self.sh.run('git symbolic-ref HEAD').stdout.strip()
        except CalledProcessError:
            raise self.UnknownCurrentBranchException

        refs_heads = 'refs/heads/'
        assert head.startswith(refs_heads)
        head = head[len(refs_heads):]
        return head

    def hasBranch(self, branch):
        p = self.sh.run_args(['git', 'rev-parse', 'refs/heads/'+branch], check=False)
        return p.returncode == 0
