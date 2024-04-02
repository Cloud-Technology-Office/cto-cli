from subprocess import run, CompletedProcess, DEVNULL


def run_command(
    command: str, check: bool = True, capture_output: bool = False, env=None, output: bool = False
) -> (CompletedProcess)[bytes]:
    if capture_output:
        output = True

    args = {'check': check, 'capture_output': capture_output, 'env': env}

    if output is False:
        args['stdout'] = DEVNULL
        args['stderr'] = DEVNULL

    return run(command, shell=True, **args)
