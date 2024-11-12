#!/usr/bin/python3

import argparse
import contextlib
import os
import shlex
import subprocess
import sys
from argparse import RawTextHelpFormatter
from datetime import datetime
from urllib.parse import urlencode, urlparse

from jinja2 import Template
from mailutil import MailUtil
from reconfig import Config
from redashapi import Redash
from requests.exceptions import HTTPError

TS_FORMAT = "%Y-%m-%dT%H:%M"


@contextlib.contextmanager
def remember_cwd():
    curdir = os.getcwd()
    try:
        yield
    finally:
        os.chdir(curdir)


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__))
    try:
        buildinfo = open(".build", "r", encoding="utf-8").read()  # pylint: disable=R1732
    except FileNotFoundError:
        buildinfo = ""
    parser = argparse.ArgumentParser(description=buildinfo, formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        "config",
        nargs="?",
        default="report.yaml",
        help="YAML configuration map (default: %(default)s)",
    )
    parser.add_argument("--dry-run", action="store_true", default=False, help="Don't send mail")
    parser.add_argument(
        "--print", action="store_true", default=False, help="Print config map and exit"
    )
    parser.add_argument(
        "--verbose", action="store_true", default=False, help="Print external commands"
    )
    args = parser.parse_args()

    cfg = Config.from_file(args.config)
    if args.print:
        print(cfg)
        sys.exit(0)

    cfg.validate()
    redash_url = cfg["redash_url"]
    redash = Redash(f"{redash_url}/api", cfg["redash_key"])

    tmpdir = os.path.join("reports", datetime.now().strftime(TS_FORMAT))
    os.makedirs(tmpdir, exist_ok=True)

    for report in cfg["reports"]:
        (dashboard_id, dashboard_slug) = redash.dashboard_id(report["dashboard"])
        public_url = redash_url + urlparse(redash.dashboard_public_url(dashboard_id)).path

        try:
            parameters = report.get("parameters", {None: [None]})  # iterate once
            assert (
                len(parameters.keys()) == 1
            ), f"{report['dashboard']}: only one type of parameter may be specified"
            key = list(parameters.keys())[0]

            for parameter in parameters[key]:
                if parameter:
                    dashboard = f"{report['dashboard']} - {parameter}"
                else:
                    dashboard = format(report["dashboard"])

                sm = MailUtil(
                    cfg["mailhost_url"],
                    From=cfg["sender"],
                    To=",".join(report["recipients"]),
                    Subject=dashboard,
                )

                if parameter:
                    parameter_key = "p_{key}"
                    qs = urlencode({parameter_key: parameter})
                else:
                    qs = ""

                report[
                    "dashboard_url"
                ] = f"{redash_url}/dashboards/{dashboard_id}-{dashboard_slug}?{qs}"
                if redash.is_shared[dashboard_id]:
                    report["dashboard_public_url"] = f"{public_url}{qs}"
                else:
                    report["dashboard_public_url"] = ""
                body = Template(cfg["message_body"]).render(**report)

                sm.set_body(body + "\n\n")

                if parameter:
                    pdf_filename = f"{report['dashboard']} - {parameter}.pdf"
                else:
                    pdf_filename = f"{report['dashboard']}.pdf"
                cmd = [
                    "node",
                    "save-report.js",
                    "--url",
                    public_url,
                    "--output",
                    os.path.join(tmpdir, pdf_filename),
                ]
                if parameter:
                    cmd.extend(["--param", f"{key}={parameter}"])
                if cfg["render_delay"] > 0:
                    cmd.extend(["--delay", str(cfg["render_delay"])])

                if args.verbose:
                    print(shlex.join(cmd))
                subprocess.check_call(cmd)  # nosec

                with remember_cwd():
                    os.chdir(tmpdir)
                    sm.attach(pdf_filename, mimetype="application/pdf")

                attachments = report.get("attachments", [])
                for redash_query in attachments:
                    q_name = redash_query["query"]
                    q_extra = redash_query.get("extra_parameters", {})
                    if parameter:
                        csv_filename = f"{q_name} - {parameter}.csv"
                    else:
                        csv_filename = f"{q_name}.csv"

                    # find default values for each query and replace the
                    # dashboard-level parameters and query-specific overrides
                    (query_id, query_params) = redash.dashboard_widget(dashboard_id, q_name)
                    if parameter:
                        query_params[key] = parameter
                    query_params.update(q_extra)

                    try:
                        result_id = redash.initiate_query(query_id, query_params)
                        cmd = [
                            "curl",
                            "-sS",
                            "-k",
                            "-o",
                            os.path.join(tmpdir, csv_filename),
                            f"{redash_url}/api/query_results/{result_id}.csv?api_key={cfg['redash_key']}",
                        ]
                    except HTTPError as ex:
                        print(ex.args[0])
                        continue

                    if args.verbose:
                        print(shlex.join(cmd))
                    subprocess.check_call(cmd)  # nosec

                    with remember_cwd():
                        os.chdir(tmpdir)
                        sm.attach(csv_filename, mimetype="text/csv")

                if not args.dry_run:
                    print("Connect to", sm)
                    sm.send_smtp()
        finally:
            redash.dashboard_reset(dashboard_id)
