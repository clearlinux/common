import subprocess, shlex

class Shell:
    # Default options passed to subprocess.run. May be customized per-instance.
    cwd = None
    check = True
    capture_output = True
    text = True

    def __init__(self, cwd=None):
        if cwd: self.cwd = cwd

    def run_args(self, args, **kwargs):
        kwargs1 = {
                'check': self.check,
                'capture_output': self.capture_output,
                'text': self.text,
                'cwd': self.cwd
                }
        kwargs1.update(kwargs)
        return subprocess.run(args, **kwargs1)

    def run(self, cmd, **kwargs):
        return self.run_args(shlex.split(cmd), **kwargs)

    def popen(self, args, **kwargs):
        return subprocess.Popen(args, cwd=self.cwd, **kwargs)
