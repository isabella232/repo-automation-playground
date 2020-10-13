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

import os
from typing import List, Tuple

from ast_parser.lib import file_utils

import constants

import yaml


def validate_yaml_syntax(
    root_dir: str,
    grep_tags: List[str],
    source_tags: List[str]
) -> Tuple[bool, List[str]]:
    yaml_paths = file_utils.get_yaml_files(root_dir)
    is_valid = True

    seen_region_tags = set()

    output = []

    # Validate region tags
    for yaml_path in yaml_paths:
        with open(yaml_path, 'r') as file:
            yaml_contents = '\n'.join(file.readlines())
            parsed_yaml = yaml.safe_load(yaml_contents)

            for tag in parsed_yaml.keys():
                yaml_entry = parsed_yaml[tag]
                tag_should_be_in_source = not (
                    'tested' in yaml_entry and yaml_entry['tested'] is False)

                # Verify mentioned region tags are used in the
                # source code (via parsing and/or grep results)
                if tag not in grep_tags:
                    output.append(
                        f'Yaml file {yaml_path} contains region '
                        f'tag not used in source files: {tag}')
                    is_valid = False
                elif tag_should_be_in_source and tag not in source_tags:
                    output.append(
                        f'Yaml file {yaml_path} contains '
                        f'unparsed region tag: {tag}')
                    output.append(
                        '  Remove it, or label it with "tested: false".')
                    is_valid = False
                elif not tag_should_be_in_source and tag in source_tags:
                    output.append(f'Parsed tag {tag} in file'
                                  f'{yaml_path} marked untested!')
                    is_valid = False

                # Verify region tags are present at most once
                if tag in seen_region_tags:
                    output.append(f'Region tag {tag} is used multiple '
                                  'times in .drift-data.yml files!')
                    is_valid = False
                else:
                    seen_region_tags.add(tag)

    # Validate individual attributes
    for yaml_path in yaml_paths:
        with open(yaml_path, 'r') as file:
            yaml_contents = '\n'.join(file.readlines())
            parsed_yaml = yaml.safe_load(yaml_contents)

            for tag in parsed_yaml.keys():
                yaml_entry = parsed_yaml[tag]

                attr = [entry for entry in yaml_entry
                        if entry in constants.RESERVED_YAML_KEYS]
                if attr:
                    attr = attr[0]
                attr_is_valid = True

                if attr and attr in constants.REQUIRED_KEY_VALUES:
                    actual = yaml_entry[attr]
                    expected = constants.REQUIRED_KEY_VALUES[attr]
                    if actual != expected:
                        attr_is_valid = False
                        is_valid = False
                        output.append(
                            f'Invalid {attr} value in file {yaml_path} '
                            f'for tag {tag}: {actual}, expected {expected} '
                            ' (or omission)')

                # Validate additions field
                if attr == 'additions':
                    if not isinstance(yaml_entry[attr], list):
                        # additions field must be an array
                        output.append(f'Additions key for {tag} in '
                                      f'{yaml_path} is not a list!')
                        attr_is_valid = False
                        is_valid = False
                    elif any(t not in grep_tags for t in yaml_entry[attr]):
                        # added tags must be correctly parsed from the codebase
                        output.append(f'Yaml file {yaml_path} contains region '
                                      f'tag not used in source files: {tag}')
                        attr_is_valid = False
                        is_valid = False

                # Validate manually-specified tests
                yaml_dirname = os.path.dirname(yaml_path)
                test_paths_exist = True
                for test_path in yaml_entry.keys():
                    if test_path in constants.RESERVED_YAML_KEYS:
                        continue  # Skip non-filepaths

                    if not os.path.isabs(test_path):
                        test_path = os.path.join(yaml_dirname, test_path)
                    if not os.path.exists(test_path):
                        output.append(f'Test file {test_path} used '
                                      f'in {yaml_path} not found!')
                        is_valid = False
                        test_paths_exist = False
                if test_paths_exist:
                    continue

                # Bad YAML format (unknown error)
                if is_valid:
                    output.append(
                        f'Region tag {tag} in file {yaml_path} '
                        'is formatted incorrectly!')
                    is_valid = False

                # Messaging for invalid attrs
                if not attr_is_valid:
                    output.append(f'Invalid {attr} key in file {yaml_path}')

    return (is_valid, output)
