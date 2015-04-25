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
ansible-playbook-debugger is the tool to debug a playbook. This debugger is
invoked when the task in the playbook fails, and enables you to check actually
used module's args, variables, facts, and so on. Also, you can fix module's args
in the debugger, and re-run the failed task (and if it is successful, the
remaining part of the playbook runs).

See https://github.com/ks888/ansible-playbook-debugger for more details.
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
