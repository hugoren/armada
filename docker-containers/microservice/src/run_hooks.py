#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import errno
import logging
import subprocess
from glob import glob
from logging.handlers import TimedRotatingFileHandler

REGISTERED_HOOKS = ('pre-stop', )
HOOKS_PATH_WILDCARD = '/opt/*/hooks'
HOOKS_LOG_PATH = '/var/log/armada/hooks'


def _get_hook_files(hook_name):
    global HOOKS_PATH_WILDCARD
    files = os.path.join(HOOKS_PATH_WILDCARD, hook_name, '*')
    for hook_file_path in sorted(glob(files)):
        if not os.path.isdir(hook_file_path):
            yield hook_file_path


def _mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno != errno.EEXIST or not os.path.isdir(path):
            raise


def _get_logger(logger_name):
    global HOOKS_LOG_PATH
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(levelname)s - %(asctime)s - %(name)s - %(message)s', '%Y-%m-%d %H:%M:%S'
    )

    if not os.path.exists(HOOKS_LOG_PATH):
        _mkdir(HOOKS_LOG_PATH)

    path = os.path.join(HOOKS_LOG_PATH, '{}.log'.format(logger_name))
    handler = TimedRotatingFileHandler(path, when='midnight', backupCount=3)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def run(hook_name):
    logger = _get_logger(hook_name)
    for path in _get_hook_files(hook_name):
        os.chmod(path, 0o755)
        os.system('sync')
        logger.info('Executing hook: {}'.format(path))
        try:
            output = subprocess.check_output([path])
        except (OSError, subprocess.CalledProcessError) as e:
            logger.error('Error: {}'.format(e))
        else:
            logger.info('result: {}'.format(output))


if __name__ == "__main__":
    root_logger = _get_logger('run_hooks')
    if len(sys.argv) != 2:
        root_logger.error(
            'Invalid number of parameters. '
            'Please provide hook name as a first parameter.'
            .format(len(sys.argv))
        )
        sys.exit(1)

    name = sys.argv[1]
    if name not in REGISTERED_HOOKS:
        root_logger.error(
            'There is no registered hook called: {}'.format(name)
        )
    else:
        run(name)
