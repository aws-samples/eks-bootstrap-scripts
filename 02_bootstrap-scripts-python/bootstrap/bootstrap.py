# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
#!/usr/bin/env python
__version__ = "0.1.5"
import sys
import argparse
import ruamel.yaml
from os import path, environ
from .context import HelmValuesBuilder, FileContext
from .helm import Helm
from .macros import addHelmValues
def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTION] [ACTION]",
        description="The cli for the bootstrap will run a helm update with values sourced from additional contexts like SSM parameters or certain environment variables. npm bin should be in your path. The script takes the following flags"
    )
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json", help="The path to the config JSON for setting up values from config files")
    parser.add_argument(
        "--artifact", help="The path to the output JSON from the stages containing stack output. This is required if --json is specified")
    parser.add_argument(
        "--context", help="A context to register with helm, see details below. This flag can be set multiple times", nargs='*', action='append')
    parser.add_argument(
        "--chart", help="Path to the helm chart to deploy, if not the application will pull the chart depending on the flags.")
    parser.add_argument(
        "--values", help="Path to values file (if not using the one at the root of the chart.")
    parser.add_argument("--release", help="Helm release name", required=True)
    parser.add_argument(
        "--print_values", help="Print generated values.", action='store_true')
    parser.add_argument("--helm", help="Deploy Helm Chart.",
                        action='store_true')
    parser.add_argument("--bindserviceaccounts",
                        help="Allow Helm to provision and bind IAM roles to K8S service accounts", action='store_true')
    parser.add_argument(
        "--helm_arg", help="Arguments to be passed to the helm upgrade command", nargs='*', action='append')
    parser.add_argument(
        '--upgrade', help='Upgrade the chart release.', action='store_true')
    parser.add_argument(
        '--template', help='Print the generated template.', action='store_true')
    return parser


def print_values_yaml(values: dict):
    res = ""
    for line in ruamel.yaml.round_trip_dump(values, indent=5, block_seq_indent=3).splitlines(True):
        res += line
    print(res)


def main() -> None:
    parser = init_argparse()
    args = parser.parse_args()
    helm_exe = Helm()
    helm_context = HelmValuesBuilder()
    command_instance = helm_exe.get_command_instance()
    values_file = None
    if args.values is not None:
        values_file = args.values
    if args.upgrade:
        command_instance.set_main_arg("upgrade")
        command_instance.set_release(args.release)
        command_instance.add_args("-i")
    elif args.template:
        command_instance.set_main_arg("template")
    if args.chart is not None:
        command_instance.set_chart(args.chart)
        if values_file is None:
            values_file = path.join(args.chart, "values.yaml")
        helm_context.add_context(
                FileContext(values_file, {'type': 'yaml'}))
        f = None
    else:
        chart_path, f = helm_exe.pullHelmChart(
            environ.get("HELM_IMAGE_TAG", default="latest"))
        command_instance.set_chart(chart_path)
        if values_file is None:
            values_file = path.join(chart_path, "values.yaml")
        helm_context.add_context(
                FileContext(values_file, {'type': 'yaml'}))
        addHelmValues(args.json, args.artifact, helm_context)

    if args.helm_arg is not None:
        print("printing arguments")
        argumentList = []
        for argument in args.helm_arg:
            argumentList.extend(argument[0].split())
        print(argumentList)
        command_instance.add_args(*argumentList)
    if args.context is not None:
        for context in args.context:
            helm_context.add_context_from_string(context[0])
    values = helm_context.get_values()
    if args.print_values:
        print("Using Values:")
        print_values_yaml(values)
    v_path = helm_exe.generate_values_file(values)
    print("Using values file at: " + v_path)
    command_instance.set_values(v_path)
    command_instance.run(force_output=True)
    if f is not None:
        f.cleanup()
    sys.exit(command_instance.exit_code)
