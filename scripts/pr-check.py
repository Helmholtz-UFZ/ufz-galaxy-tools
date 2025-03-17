import sys
import yaml

from bioblend import toolshed 

ts = toolshed.ToolShedInstance(url='https://toolshed.g2.bx.psu.edu')
fn = sys.argv[1]

# never mind about fancy yaml linting, let's just make sure the files are openable
sys.stdout.write('Checking modified yaml file {}...\n'.format(fn))
with open(fn) as f: 
    yml = yaml.safe_load(f)['tools']

with open('{}.lock'.format(fn)) as f:
    yml_lock_names = [n['name'] for n in yaml.safe_load(f)['tools']]

new_tools = [t for t in yml if t["name"] not in yml_lock_names]

for tool in new_tools:  # check all new tools are in the tool shed
    sys.stdout.write('Checking new tool {} is in the toolshed...\n'.format(tool))
    search_hits = ts.repositories.get_repositories(tool["name"], tool["owner"])
    assert len(search_hits) == 1, '{} not in toolshed.'.format(tool)
    assert tool["name"] in search_hits[0]["name"]
