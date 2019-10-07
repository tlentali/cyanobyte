# Copyright (C) 2019 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Command-line tool to generate source files from Jinja templates.
"""
import os
import re
import sys
import shutil
import click
from yaml import load

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
from jinja2 import Environment, FileSystemLoader

_VERSION = "0.1.0"
_DEBUG = False
_CLEAN = False

def camel_to_snake(camel_str):
    """
    Converts a camelCaseString into a snake_case_string
    """
    regex = re.compile('([A-Z])')
    result = regex.sub(r'_\g<0>', str(camel_str))
    return result.lower()

def generate_source_file(template, peripheral, template_extension, output_dir):
    """
    Generates a source file for a provided Jinja2 template.

    Args:
        template: A single file that is part of the template.
        peripheral: A single CyanoByte document to generate.
        template_extension: The file extension of the output.
        output_dir: The directory to output the generated files.
    """
    # Open peripheral file
    with open(peripheral, "r") as peripheral_file:
        peripheral_data = load(peripheral_file, Loader=Loader)
        # Add additional metadata to the spec data
        peripheral_data["version"] = _VERSION
        peripheral_data["fileName"] = peripheral

        if _DEBUG:
            print(peripheral_data)

        # Render file
        peripheral_gen = template.render(peripheral_data)
        # Get file path
        # Take into consideration the package
        if _DEBUG:
            print(peripheral_data["info"]["title"])
        package_path = peripheral_data["info"]["package"].replace(".", "/")
        output_file_path = os.path.join(
            output_dir,
            os.path.normpath(package_path)
        )
        if not os.path.exists(output_file_path):
            try:
                os.makedirs(output_file_path)
            except OSError:
                print("Could not make file directory", output_file_path)
                sys.exit(1)

        peripheral_output_path = os.path.join(
            output_file_path,
            peripheral_data["info"]["title"] + template_extension
        )
        with open(peripheral_output_path, "x") as peripheral_output_file:
            peripheral_output_file.write(peripheral_gen)


def generate_files_for_template(env, template_file, input_files, output_dir):
    """
    Generates a series of source files for a provided template file.

    Args:
        env: Jinja2 environment used during generation.
        template_file: A single file that is part of the template.
        input_files: A list of CyanoByte documents to generate.
        output_dir: The directory to output the generated files.
    """
    # Open template
    with open(template_file, "r") as template_contents:
        template_object = env.from_string(template_contents.read())
        _, template_extension = os.path.splitext(template_file)

        # Create output dir
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError:
                print("Could not make output directory", output_dir)
                sys.exit(1)

        for peripheral in input_files:
            generate_source_file(
                template_object, peripheral, template_extension, output_dir
            )


@click.command()
@click.option("-i", "--input", "input_files", multiple=True)
@click.option("-t", "--template", "template_files", multiple=True)
@click.option("-o", "--output", "output_dir", default="./build",
              show_default=True)
@click.option("-d", "--debug", "debug", default=False)
@click.option("-c", "--clean", "clean", is_flag=True)
def gen(input_files, template_files=None, output_dir='./build', debug=False,
        clean=False):
    """
    Takes command line arguments and generates source files for every
    peripheral to each template file.

    Args:
        input_files: A list of CyanoByte documents to generate.
        template_files: A list of files that are part of the template.
        output_dir: The directory to output the generated files.
        debug: Print debug messages?
        clean: Clean the output directory before output?
    """
    #pylint: disable=global-statement
    global _DEBUG
    _DEBUG = debug

    if _DEBUG:
        print("Generating " + str(len(input_files)) + " file(s)")

    # Removes any files in the directory if clean flag is set
    if clean and os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader("./templates"),
        trim_blocks=True,
        lstrip_blocks=True
    )
    env.filters['camel_to_snake'] = camel_to_snake
    for template_file in template_files:
        generate_files_for_template(
            env,
            template_file,
            input_files,
            output_dir
        )


if __name__ == "__main__":
    gen(sys.argv[1:])
