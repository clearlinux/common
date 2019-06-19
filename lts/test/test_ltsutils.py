import unittest
import os, pathlib, tempfile, logging
import subprocess, functools

from ltsutils.package_repo import PackageRepo
import ltsutils.shell

run = functools.partial(subprocess.run, check=True)

class Package:
    def __init__(self, name):
        self.name = name
        self.repo_url = 'https://github.com/clearlinux-pkgs/{}.git'.format(name)

class LTSUtilsTestCase(unittest.TestCase):
    toplvl = pathlib.Path('../../..')
    packages = toplvl / 'packages'

    def cloneOrExtractRepo(self):
        tmpdir = pathlib.Path('/var/tmp/common-lts-test')
        tmpdir.mkdir(mode=0o700, exist_ok=True)
        tarball = tmpdir / '{}.tar.gz'.format(self.package.name)
        if tarball.exists():
            run(['tar', 'xf', tarball, '-C', self.workdir])
        else:
            run(['git', 'clone', self.package.repo_url, self.workdir])
            run(['tar', 'czf', tarball, '-C', self.workdir, '.'])

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory(prefix='test-{}-'.format(self.package.name), dir=self.packages)
        self.workdir = pathlib.Path(self._tmpdir.name)
        self.cloneOrExtractRepo()
        self.repo = PackageRepo(self.package.name, self.workdir)

        self._sh = ltsutils.shell.Shell(self.workdir)
        self._sh.capture_output = False

    def sh(self, cmd):
        return self._sh.run(cmd)

    def sh_stdout(self, cmd):
        return self._sh.run(cmd, capture_output=True).stdout.rstrip()

    def tearDown(self):
        self._tmpdir.cleanup()

class PackageRepoTestCase(LTSUtilsTestCase):
    def setUp(self):
        super().setUp()
        self.L1 = self.package.L1
        self.L2 = self.package.L2
        self.sh('git branch L1 %s' % self.L1)
        self.sh('git branch L2 %s' % self.L2)

    def testGetNVR(self):
        raise NotImplementedError

    def testHasBranch(self):
        self.assertTrue(self.repo.hasBranch('L2'))
        self.assertFalse(self.repo.hasBranch('L3'))

    def testCheckoutBranch(self):
        self.repo.checkoutBranch('L2')
        self.assertEqual(self.sh_stdout('git rev-parse HEAD'), self.L2)

        self.assertRaises(PackageRepo.InvalidBranchException, self.repo.checkoutBranch, 'L3')

    def testFastForward(self):
        self.repo.fastForwardBranch('L1', 'L2')
        self.assertEqual(self.sh_stdout('git rev-parse L1'), self.L2)
        self.assertEqual(self.sh_stdout('git rev-parse L2'), self.L2)

    def testGetCurrentBranch(self):
        self.repo.checkoutBranch('L2')
        b = self.repo.getCurrentBranch()
        self.assertEqual(b, 'L2')

        self.sh('git checkout --detach L2')
        self.assertRaises(PackageRepo.UnknownCurrentBranchException, self.repo.getCurrentBranch)

class TestNano(PackageRepoTestCase):
    package = Package('nano')
    package.L1 = '3dcfa09f5217eedf6ec7539af7e243655d3abdb6' # 3.2-54
    package.L2 = 'b8243dd54e8feb16a11474f848b8735f5591cf12' # 3.2-55

    def testGetNVR(self):
        nvr = self.repo.getNVR(self.L2)
        self.assertEqual(nvr, ('nano', '3.2', '55'))

class TestMySQL_Python(PackageRepoTestCase):
    package = Package('MySQL-python')
    package.L1 = '386163d8fc9c857c7194c4e958374af4c4f071ed' # 1.2.5-31
    package.L2 = 'f85bc5ec2141384f45f224d4464a0a44a981a4d4' # 1.2.5-33

    def testGetNVR(self):
        nvr = self.repo.getNVR(self.L2)
        self.assertEqual(nvr, ('MySQL-python', '1.2.5', '33'))
