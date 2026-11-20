#!/usr/bin/env python
"""Sanity check for one tool section file.

Verifies that
* the (human edited) section file and its lock file are loadable,
* every tool that is listed in the section file but not yet in the lock file
  actually exists in the Tool Shed.

Deltas vs. the upstream ``galaxy_tools_management_template`` script:
* repositories are looked up by *name and owner* (the upstream version searched
  by name only and therefore accepted tools from the wrong owner),
* a missing ``<file>.lock`` is treated as empty so that brand new sections do
  not crash PR linting (``make fix`` creates the lock file).
"""

import os
import sys

import yaml

from bioblend import toolshed

ts = toolshed.ToolShedInstance(url='https://toolshed.g2.bx.psu.edu')
fn = sys.argv[1]

sys.stdout.write('Checking modified yaml file {}...\n'.format(fn))
with open(fn) as f:
    yml = [(t['owner'], t['name']) for t in yaml.safe_load(f)['tools']]

lock_fn = '{}.lock'.format(fn)
if os.path.exists(lock_fn):
    with open(lock_fn) as f:
        yml_lock = [(t['owner'], t['name']) for t in yaml.safe_load(f)['tools']]
else:
    sys.stdout.write('No lock file {}, treating it as empty...\n'.format(lock_fn))
    yml_lock = []

new_tools = [t for t in yml if t not in yml_lock]

for owner, name in new_tools:  # check all new tools are in the tool shed
    sys.stdout.write('Checking new tool {}/{} is in the toolshed...\n'.format(owner, name))
    search_hits = ts.repositories.get_repositories(name=name, owner=owner)
    assert len(search_hits) == 1, '{}/{} not uniquely in toolshed: {}'.format(
        owner, name, [hit.get('name') for hit in search_hits]
    )
    assert search_hits[0]['name'] == name, '{}/{} not in toolshed.'.format(owner, name)
