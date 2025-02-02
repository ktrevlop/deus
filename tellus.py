#!/usr/bin/env python3

# Copyright © 2021-2022 Helmholtz Centre Potsdam GFZ German Research Centre for
# Geosciences, Potsdam, Germany
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.
"""
Module for all the common elements for deus and volcanus.
Name comes from https://de.wikipedia.org/wiki/Tellus
"""

import glob
import json
import os

import gpdexposure
import schemamapping


class Child:
    """
    This is a tellus child class that represents
    a deus instance.
    """

    def __init__(
        self,
        intensity_provider,
        fragility_provider,
        old_exposure,
        exposure_schema,
        loss_provider,
        args_with_output_paths,
    ):
        self.intensity_provider = intensity_provider
        self.fragility_provider = fragility_provider
        self.old_exposure = old_exposure
        self.exposure_schema = exposure_schema
        self.loss_provider = loss_provider
        self.args_with_output_paths = args_with_output_paths

    def run(self):
        """
        All the work is done here.
        """
        current_dir = os.path.dirname(__file__)
        schema_mapper = create_schema_mapper(current_dir)

        result_exposure = gpdexposure.update_exposure_transitions_and_losses(
            self.old_exposure,
            self.exposure_schema,
            schema_mapper,
            self.intensity_provider,
            self.fragility_provider,
            self.loss_provider,
        )

        write_result(
            self.args_with_output_paths.merged_output_file,
            result_exposure,
        )


def create_schema_mapper(current_dir):
    """
    Creates and returns a schema mapper
    using local mapping files.
    """
    pattern_to_search_for_tax_files = os.path.join(
        current_dir, "schema_mapping_data_tax", "*.json"
    )
    tax_mapping_files = glob.glob(pattern_to_search_for_tax_files)

    pattern_to_search_for_ds_files = os.path.join(
        current_dir, "schema_mapping_data_ds", "*.json"
    )
    ds_mapping_files = glob.glob(pattern_to_search_for_ds_files)

    # fmt: off
    return schemamapping. \
        SchemaMapper. \
        from_taxonomy_and_damage_state_conversion_files(
            tax_mapping_files, ds_mapping_files
        )
    # fmt: on


def write_result(output_file, cells):
    """
    Write the updated exposure.
    """
    if os.path.exists(output_file):
        os.unlink(output_file)
    cells.to_file(output_file, "GeoJSON")
