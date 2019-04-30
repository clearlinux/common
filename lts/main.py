#!/usr/bin/python
import sys,argparse

from ltsutils.package_repo import PackageRepo

def log(msg, **kwargs):
    print(msg, file=sys.stderr)

def init_parser():
    main = argparse.ArgumentParser()
    main.add_argument('package_name', nargs=1)
    subparsers = main.add_subparsers(dest='command', metavar='command', required=True)

    p = subparsers.add_parser('checkout-prev',
            help='checkout previous branch')
    p = subparsers.add_parser('is-same-version',
            help='return true if package version is the same as the given branch')
    p.add_argument('branch', nargs=1)
    p = subparsers.add_parser('fast-forward',
            help='fast-forward current branch to a newer branch')
    p.add_argument('branch', nargs=1)

    p = subparsers.add_parser('sanity-check',
            help='run sanity checks for data consistency')

    return main

def checkout_prev(args, repo):
    active_branches = repo.getActiveBranches()
    current = repo.getCurrentBranch()

    i = active_branches.index(current)
    if i == 0:
        log('Already on oldest active branch.')
        return False

    prev = active_branches[i-1]
    repo.checkoutBranch(prev, allow_remote=True)

def is_same_version(args, other):
    current = repo.getCurrentBranch()
    other = args.branch[0]
    assert repo.hasBranch(other), 'Branch %s not found' % other

    v1, v2 = [repo.getNVR('refs/heads/'+b)[1] for b in (current, other)]
    if v1 != v2:
        log('Current version {} does not match version {} on branch {}'.format(v1, v2, other))
    return v1 == v2

def fast_forward(args, repo):
    current = repo.getCurrentBranch()
    newer = args.branch[0]

    log('Fast-forwarding {} to {}'.format(current, newer))
    repo.fastForwardBranch(current, newer)

def sanity_check(args, repo):
    ok = True
    # HEAD must point to a branch
    try:
        current = repo.getCurrentBranch()
    except PackageRepo.UnknownCurrentBranchException:
        log('Unknown current branch. Has a branch been checked out?')
        current = None
        ok = False

    # active-branches file must not be empty
    active_branches = repo.getActiveBranches()
    if not len(active_branches):
        log('No active branches defined. Is active-branches file empty?')
        ok = False
    # current branch must be an active branch
    elif current and current not in active_branches:
        log('%s is not an active LTS branch.' % current)
        ok = False

    return ok

if __name__=='__main__':
    args = init_parser().parse_args()
    repo = PackageRepo(args.package_name[0], '.')

    commands = {
            'checkout-prev': checkout_prev,
            'is-same-version': is_same_version,
            'fast-forward': fast_forward,
            'sanity-check': sanity_check,
            }
    ret = commands[args.command](args, repo)
    if ret is not None:
        exit(0 if ret else 1)
