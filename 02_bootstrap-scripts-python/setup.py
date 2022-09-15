# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""

import re
from setuptools import setup

with open("version.txt", 'r') as fh:
    version = fh.read()
    print(version)
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
install_requires = [
'ruamel.yaml==0.17.10',
'jsonpath-ng==1.5.2',
'deepmerge==0.3.0'
]
setup(
    name="bootstrap-cli",
    version=version,
    author="AWS",
    description="This is the bootstrap-cli can run a helm update with values sourced",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aws-samples/amazon-ecr-repo-creation-crossaccount.git",
    project_urls={
        "Bug Tracker": "https://github.com/aws-samples/eks-bootstrap-scripts/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT No Attribution License (MIT-0)",
        "Operating System :: OS Independent",
    ],
    packages=["bootstrap"],
    install_requires=install_requires,
    entry_points={
        "console_scripts": ['bootstrap-cli = bootstrap.bootstrap:main']
        },
    python_requires=">=3.6",
)
