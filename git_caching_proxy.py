#! /usr/bin/env python3

import subprocess
import pathlib
import shlex
import sys
import logging
import os
import urllib.parse


DEFAULT_GIT_EXEC = 'git'


stdin = sys.stdin.buffer
stdout = sys.stdout.buffer


def read_pkt_line():
    input_len = int(stdin.read(4).decode('ascii'), base=16)
    return stdin.read(input_len - 4)


def write_pkt_line(data: bytes, buffer=stdout):
    output_len = len(data) + 4
    if output_len > 0xffff:
        raise ValueError('data too long')
    buffer.write(f'{output_len:04x}'.encode('ascii'))
    buffer.write(data)


def write_error(message: str):
    logging.info('reporting error to client: %s', message)
    write_pkt_line(f'ERR {message}\n'.encode('utf-8'))


def main():
    env = os.environ
    if env.get('GIT_CACHING_PROXY_VERBOSE'):
        loglevel = logging.DEBUG
    else:
        loglevel = logging.INFO
    logging.basicConfig(
        format='%(asctime)s %(message)s',
        level=loglevel,
    )
    logging.debug('environment: %r', env)

    try:
        base_path = pathlib.Path(env.get('GIT_CACHING_PROXY_BASE_PATH', '/'))
        logging.debug('base path: %r', base_path)
        git_exec = shlex.split(env.get('GIT_CACHING_PROXY_GIT_EXEC', DEFAULT_GIT_EXEC))
        logging.debug('git executable: %r', git_exec)
        git_upstream_args = shlex.split(env.get('GIT_CACHING_PROXY_UPSTREAM_ARGS', ''))
        logging.debug('additional arguments for git upstream: %r', git_upstream_args)
        abort_on_upstream_failure = bool(env.get('GIT_CACHING_PROXY_ABORT_ON_UPSTREAM_FAILURE'))

        # intercept client's first command and extract repository URL

        first_pkt_line = read_pkt_line()
        logging.debug('first pkt-line: %r', first_pkt_line)
        service, _, args = first_pkt_line.partition(b' ')
        if service == b'git-receive-pack':
            # if client makes a push request, exit early
            write_error('write access is not allowed')
            return
        repo_url, _, remaining_args = args.partition(b'\0')
        # strip off leading slash in url
        # is utf-8 a good choice here?
        repo_url = repo_url.decode('utf-8')[1:]
        logging.info('repo url: %r', repo_url)
        url_splitted = urllib.parse.urlsplit(repo_url)
        if not url_splitted.scheme:
            write_error('url has no scheme')
        normalized_path = url_splitted.scheme + url_splitted._replace(scheme='').geturl()[1:]
        logging.debug('normalized path: %r', normalized_path)
        local_repo_path = base_path / normalized_path
        logging.info('local repository path: %r', local_repo_path)

        # either clone or fetch the upstream repository

        git_exec_args = [*git_exec, *git_upstream_args]
        if not local_repo_path.exists():
            logging.info('running git clone...')
            git_exec_args.extend(['clone', '--mirror', repo_url, local_repo_path])
            
        else:
            logging.info('running git remote update...')
            git_exec_args.extend(['-C', local_repo_path, 'remote', 'update', '--prune'])
        git_upstream_completed_process = subprocess.run(
            git_exec_args,
            stdin=subprocess.DEVNULL,
            stdout=sys.stderr,
        )
        if (returncode := git_upstream_completed_process.returncode) != 0:
            logging.warning('git upstream process exited with code %d', returncode)
            if abort_on_upstream_failure:
                write_error(f'git upstream process exited with code {returncode}')
        
        # start downstream git daemon process, feed it normalized reposity local path,
        # and relay future client commands
        
        logging.info('starting git daemon downstream process...')
        git_daemon_process = subprocess.Popen(
            [*git_exec, 'daemon',
            '--inetd', '--export-all', '--log-destination=stderr',
            '--strict-paths', local_repo_path],
            stdin=subprocess.PIPE,
        )
        stdout.close()
        downstream_stdin = git_daemon_process.stdin
        new_pkt_line = b''.join([service, b' ', str(local_repo_path).encode('utf-8'), b'\0', remaining_args])
        logging.debug('new pkt-line: %r', new_pkt_line)
        write_pkt_line(new_pkt_line, buffer=downstream_stdin)
        downstream_stdin.flush()
        logging.debug('written new pkt-line')
        while readbuf := stdin.read1():
            logging.debug('received %r', readbuf)
            downstream_stdin.write(readbuf)
            downstream_stdin.flush()
        logging.debug('eof')
        downstream_stdin.close()

    except Exception as e:
        logging.error('Unhandled exception', exc_info=True)
        if not stdout.closed:
            write_error(f'unhandled exception {e!r}')


if __name__ == '__main__':
    main()
