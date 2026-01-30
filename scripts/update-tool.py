import argparse
import copy
import glob
import logging
import os
import sys

import yaml
from bioblend import toolshed

ts = toolshed.ToolShedInstance(url="https://toolshed.g2.bx.psu.edu")


def update_file(fn, owner=None, name=None, without=False):
    success = True
    with open(fn + ".lock", "r") as handle:
        locked = yaml.safe_load(handle)

    # Update any locked tools.
    for tool in locked["tools"]:
        # If without, then if it is lacking, we should exec.
        logging.debug("Examining {owner}/{name}".format(**tool))

        if without:
            if "revisions" in tool and not len(tool.get("revisions", [])) == 0:
                continue

        if not without and owner and tool["owner"] != owner:
            continue

        if not without and name and tool["name"] != name:
            continue

        logging.info("Fetching updates for {owner}/{name}".format(**tool))
        try:
            revs = ts.repositories.get_ordered_installable_revisions(
                tool["name"], tool["owner"]
            )
        except Exception as e:
            logging.error(
                f"Could not get info for {tool['name']} ({tool['owner']}) from TS: {e}"
            )
            success = False
            continue

        if len(revs) == 0:
            logging.error(
                f"No installable revisions for {tool['name']} ({tool['owner']})"
            )
            success = False
            continue
        logging.info(f"TS revisions: {revs}")
        logging.info(f"Installed revisions: {tool.get("revisions", [])}")
        latest_rev = revs[-1]
        if latest_rev in tool.get("revisions", []):
            # The rev is already known, don't add again.
            continue

        logging.info(
            "Found newer revision of {owner}/{name} ({rev})".format(
                rev=latest_rev, **tool
            )
        )

        # Get latest rev, if not already added, add it.
        if "revisions" not in tool:
            tool["revisions"] = []

        if latest_rev not in tool["revisions"]:
            # TS doesn't support utf8 and we don't want to either.
            tool["revisions"].append(str(latest_rev))

        tool["revisions"] = sorted(list(set(tool["revisions"])))

    locked['tools'] = sorted(locked['tools'], key=lambda d: d['name'])
    with open(fn + ".lock", "w") as handle:
        yaml.dump(locked, handle, default_flow_style=False)
    return success


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("fn", type=argparse.FileType("r"), help="Tool.yaml file")
    parser.add_argument(
        "--owner",
        help="Repository owner to filter on, anything matching this will be updated",
    )
    parser.add_argument(
        "--name",
        help="Repository name to filter on, anything matching this will be updated",
    )
    parser.add_argument(
        "--without",
        action="store_true",
        help="If supplied will ignore any owner/name and just automatically add the latest hash for anything lacking one.",
    )
    parser.add_argument(
        "--log",
        choices=("critical", "error", "warning", "info", "debug"),
        default="info",
    )
    args = parser.parse_args()
    logging.basicConfig(level=getattr(logging, args.log.upper()))
    success = update_file(
        args.fn.name, owner=args.owner, name=args.name, without=args.without
    )
    if not success:
        sys.exit(1)
