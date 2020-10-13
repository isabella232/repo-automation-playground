# Copyright 2020 Google LLC. All Rights Reserved.
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


from . import analyze, cli_yaml


def __write_output(output, output_file):
    if output_file:
        with open(output_file, 'w+') as f:
            f.write('\n'.join(output))
    else:
        for o in output:
            print(o)


# Validates .drift-data.yml files in a directory
def validate_yaml(repo_json, root_dir, output_file=None):
    (grep_tags, source_tags, ignored_tags, source_methods) = \
        analyze.analyze_json(repo_json, root_dir)

    (is_valid, output) = cli_yaml.validate_yaml_syntax(
        root_dir, grep_tags, source_tags)

    if is_valid:
        output.append('All files are valid.')
    else:
        output.append('Invalid file(s) found!')

    __write_output(output, output_file)
