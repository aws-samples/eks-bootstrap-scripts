# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
from os import environ, path, getcwd, chdir
from typing import Tuple
from shutil import which
import json
import subprocess
import sys
import tempfile
from ruamel.yaml import YAML

_DEFAULT_REPO: str = "1234567890.dkr.ecr.us-west-2.amazonaws.com"
_HELM_DEFAULT_IMAGE: str = "helm-eks-bootstrap"

yaml = YAML(typ='safe')


class HelmInterface:
    pass


class HelmCommand:
    def __init__(self, helm: HelmInterface, main_arg="install", chart_path=None, values_path=None, release=None):
        self.main_arg = main_arg
        self.helm = helm
        self.chart_path = chart_path
        self.values_path = values_path
        self.release = release
        self.args = []
        self.exit_code = 127

    def add_args(self, *args):
        self.args.extend(args)

    def set_main_arg(self, arg: str):
        self.main_arg = arg

    def set_chart(self, c_path: str):
        self.chart_path = c_path

    def set_release(self, release: str):
        self.release = release

    def set_values(self, v_path: str):
        self.values_path = v_path

    def run(self, force_output=False):
        run_args = [self.helm.bin]
        run_args.append(self.main_arg)
        if self.release is not None:
            run_args.append(self.release)
        if self.chart_path is not None:
            run_args.append(self.chart_path)
        if self.values_path is not None:
            run_args.extend(['-f', self.values_path])
        run_args.extend(self.args)
        print(run_args)
        p = subprocess.run(run_args, capture_output=True)
        self.exit_code = p.returncode
        if self.exit_code != 0 or force_output:
            print(p.stdout.decode('unicode_escape'))
            print(p.stderr.decode('unicode_escape'), file=sys.stderr)


class Helm(HelmInterface):

    def __init__(self):
        self.bin = which("helm")

    def get_command_instance(self) -> HelmCommand:
        return HelmCommand(self)

    def pullHelmChart(self, chartVersion: str) -> Tuple[str, tempfile.TemporaryDirectory]:
        repo = environ.get("BOOTSTRAP_DEFAULT_REPO",
                           default=_DEFAULT_REPO)
        image = environ.get("BOOTSTRAP_HELM_DEFAULT_IMAGE",
                            default=_HELM_DEFAULT_IMAGE)
        image_part = "/".join([repo, image])
        image_uri = ":".join([image_part, chartVersion])
        t = tempfile.TemporaryDirectory()
        self.get_helm_image(image_uri, t.name)
        return path.join(t.name, "helm-eks-bootstrap"), t

    def get_helm_image(self, image: str, targetPath: str):
        pull_cmd = self.get_command_instance()
        pull_cmd.set_main_arg("chart")
        pull_cmd.add_args("pull", image)
        pull_cmd.run()
        export_cmd = self.get_command_instance()
        export_cmd.set_main_arg("chart")
        export_cmd.add_args("export", image)
        old_dir = getcwd()
        chdir(targetPath)
        export_cmd.run()
        chdir(old_dir)

    def generate_values_file(self, values: dict):
        values_path = None
        with tempfile.NamedTemporaryFile('w', delete=False) as values_file:
            yaml.dump(values, values_file)
            values_path = values_file.name
        return values_path
