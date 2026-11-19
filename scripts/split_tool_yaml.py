#!/usr/bin/env python

import yaml
from collections import defaultdict
import re
import os
import string
import argparse


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    rval = ''
    for c in value:
        rval += (c if c in string.ascii_letters + string.digits else '_').lower()
    return rval


def strip_superflous(cat):
    """
    Re-arranges the ephemeris returned yml format for tools to the usegalaxy-tools minimal tool yml format

    i.e. Takes a list like:

    - name: substitution_rates
      owner: devteam
      revisions:
      - d1b35bcdaacc
      tool_panel_section_label: Regional Variation
      tool_shed_url: toolshed.g2.bx.psu.edu
    - name: indels_3way
      owner: devteam
      revisions:
      - 5ad24b81dd10
      tool_panel_section_label: Regional Variation
      tool_shed_url: toolshed.g2.bx.psu.edu

      ...

     and returns:

     tool_panel_section_label: Regional Variation
     - name: substitution_rates
       owner: devteam
     - name: indels_3way
       owner: devteam

       ...
    """

    out = {'tool_panel_section_label': cat[0]['tool_panel_section_label'].strip()}

    for tool in cat:
        if 'tool_panel_section_label' in tool:
            del tool['tool_panel_section_label']
        if 'tool_panel_section_id' in tool:
            del tool['tool_panel_section_id']
        if 'revisions' in tool:
            del tool['revisions']
        if 'tool_shed_url' in tool and \
            tool['tool_shed_url'] in ['toolshed.g2.bx.psu.edu', 'https://toolshed.g2.bx.psu.edu']:
            del tool['tool_shed_url']

    out['tools'] = cat

    return out

# Adapted from ephemeris
def reduce_tool_list(tool_list):
    changes_in_tool_list = True
    while changes_in_tool_list:
        changes_in_tool_list = False
        for current_tool in tool_list:
            for tool in tool_list:
                if current_tool is tool:
                    continue
                if (
                    tool["name"] == current_tool["name"]
                    and tool["owner"] == current_tool["owner"]
                ):
                    if 'revisions' in current_tool and 'revisions' in tool:
                        current_tool["revisions"].extend(tool["revisions"])
                    tool_list.remove(tool)
                    changes_in_tool_list = True
            if 'revisions' in current_tool:
                current_tool["revisions"] = list(set(current_tool["revisions"]))
    return tool_list

def main():

    VERSION = 0.2

    parser = argparse.ArgumentParser(description="Splits up a Ephemeris `get_tool_list` yml file for a Galaxy server into individual files for each Section Label.")
    parser.add_argument("-i", "--infile", help="The returned `get_tool_list` yml file to split.")
    parser.add_argument("-o", "--outdir", help="The output directory to put the split files into. Defaults to infile without the .yml.")
    parser.add_argument("-l", "--lockfiles", action='store_true', help="Produce lock files instead of plain yml files.")
    parser.add_argument("--version", action='store_true')
    parser.add_argument("--verbose", action='store_true')

    args = parser.parse_args()

    if args.version:
        print("split_tool_yml.py version: %.1f" % VERSION)
        return

    filename = args.infile

    a = yaml.safe_load(open(filename, 'r'))
    outdir = re.sub(r'\.yml', '', filename)
    if args.outdir:
        outdir = args.outdir

    if args.verbose:
        print('Outdir: %s' % outdir)
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    tools = a['tools']
    categories = defaultdict(list)

    for tool in tools:
        categories[tool.get('tool_panel_section_label', 'Other').strip()].append(tool)

    for cat in categories:
        fname = str(cat)
        good_fname = outdir + "/" + slugify(fname) + ".yml"
        if args.lockfiles:
            good_fname += ".lock"
        if os.path.exists(good_fname):
            with open(good_fname) as f:
                current_yaml_dict = yaml.safe_load(f)
            categories[cat] += current_yaml_dict['tools']
        # Remove duplicates:
        reduce_tool_list(categories[cat])
        # Keep the output deterministic / alphabetical (delta vs. upstream template).
        categories[cat].sort(key=lambda t: (t['name'], t['owner']))
        if args.lockfiles:
            tool_yaml = {'tools': categories[cat]}
        else:
            tool_yaml = strip_superflous(categories[cat])
        if args.verbose:
            print("Working on: %s" % good_fname)
        with open(good_fname, 'w') as outfile:
            yaml.dump(tool_yaml, outfile, default_flow_style=False)

    return


if __name__ == "__main__":
    main()
