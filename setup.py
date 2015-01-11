#!/usr/bin/env python

import os
import sys
sys.path.insert(0, os.path.abspath('lib'))
from setuptools import setup, find_packages

from ansibledebugger import __version__

classifiers = [
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    'Programming Language :: Python',
    'Topic :: Software Development',
    'Topic :: Software Development :: Debuggers',
    'Topic :: System :: Systems Administration',
]

setup(
    name='ansible-playbook-debugger',
    version=__version__,
    description='Debugger for Ansible Playbook',
    long_description="""
Although Ansible is a powerful tool for configuration management, debugging its
playbook is often bothersome. One of its reasons is an error message from
ansible may not include enough information for debug. For example, variables and
task's keywords are not included usually. Another reason is the time it takes to
run a playbook. It may take a long time, and you may need to run the playbook
several times to get more details and to see that the bug is fixed.

ansible-playbook-debugger is the debugger to facilitate such a bothersome work.
When a task fails, the debugger is invoked automatically. Then you can check
the module's arguments, variables, keywords, and so on. Furthermore, you can
change the module's arguments to fix a bug, and re-execute the task. If the
re-execution is successful, the playbook continues to run as if there was no
error.
""",
    classifiers=classifiers,
    author='Kishin Yagami',
    author_email='k.yagami.suou@gmail.com',
    url='https://github.com/ks888/ansible-playbook-debugger',
    license='GPLv3',
    install_requires=['ansible'],
    packages=find_packages('lib'),
    package_dir={'ansibledebugger': 'lib/ansibledebugger'},
    scripts=[
        'bin/ansible-playbook-debugger',
    ],
    zip_safe=False,
)
