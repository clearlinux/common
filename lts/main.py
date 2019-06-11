#!/usr/bin/python
import sys,argparse

from ltsutils.package_repo import PackageRepo

def log(msg, **kwargs):
    print(msg, file=sys.stderr)

def init_parser():
    main = argparse.ArgumentParser()
    main.add_argument('package_name', nargs=1)
    subparsers = main.add_subparsers(dest='command', metavar='command', required=True)

    # Package maintenance commands
    p = subparsers.add_parser('prev-branch',
            help='show previous branch')
    p.add_argument('--checkout', action='store_true', help='checkout the branch')
    p = subparsers.add_parser('next-branch',
            help='show next branch')
    p.add_argument('--checkout', action='store_true', help='checkout the branch')
    p = subparsers.add_parser('current-branch',
            help='show current branch')
    p = subparsers.add_parser('is-same-version',
            help='return true if package version is the same as the given branch')
    p.add_argument('branch', nargs=1)
    p = subparsers.add_parser('fast-forward',
            help='fast-forward current branch to a newer branch')
    p.add_argument('branch', nargs=1)

    # RPM build commands
    p = subparsers.add_parser('can-reuse-binary',
            help='check if binary from another branch can be used in current branch')
    p.add_argument('branch', nargs=1)

    # Other commands
    p = subparsers.add_parser('prompt',
            help='prompt user to continue and return appropriate exit code')
    p = subparsers.add_parser('sanity-check',
            help='run sanity checks for data consistency')

    return main

def prev_branch(args, repo):
    active_branches = repo.getActiveBranches()
    current = repo.getCurrentBranch()

    i = active_branches.index(current)
    if i == 0:
        log('Already on oldest active branch.')
        return False

    prev = active_branches[i-1]
    print(prev)
    if args.checkout:
        repo.checkoutBranch(prev, allow_remote=True)

def next_branch(args, repo):
    active_branches = repo.getActiveBranches()
    current = repo.getCurrentBranch()

    i = active_branches.index(current)
    if i == len(active_branches)-1:
        log('Already on newest active branch.')
        return False

    next_ = active_branches[i+1]
    print(next_)
    if args.checkout:
        repo.checkoutBranch(next_, allow_remote=False)

def current_branch(args, repo):
    current = repo.getCurrentBranch()
    print(current)

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

def can_reuse_binary(args, repo):
    # Just compare versions for now
    # TODO: ABI compatibility testing
    current = repo.getCurrentBranch()
    older = args.branch[0]
    v1, v2 = [repo.getNVR('refs/heads/'+b)[1] for b in (older, current)]
    return v1 == v2

def prompt(args, repo):
    import selectors
    timeout = 60

    while True:
        print('Continue? (y/N): ', end='', flush=True)
        with selectors.DefaultSelector() as sel:
            sel.register(sys.stdin, selectors.EVENT_READ)
            events = sel.select(timeout)
        if not len(events):
            print('Timed out after {}s.'.format(timeout))
            return False
        else:
            s = sys.stdin.readline().rstrip('\n')
            if s in ('Y', 'y', 'N', 'n', ''):
                break

    if s in ('Y', 'y'):
        return True
    else:
        print('Cancelled.')
        return False

if __name__=='__main__':
    args = init_parser().parse_args()
    repo = PackageRepo(args.package_name[0], '.')

    commands = {
            'prev-branch': prev_branch,
            'next-branch': next_branch,
            'current-branch': current_branch,
            'is-same-version': is_same_version,
            'fast-forward': fast_forward,
            'can-reuse-binary': can_reuse_binary,
            'prompt': prompt,
            'sanity-check': sanity_check,
            }
    ret = commands[args.command](args, repo)
    if ret is not None:
        exit(0 if ret else 1)
