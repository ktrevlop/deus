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
This is the Damage-Exposure-Update-Service.

Please use -h for usage.
"""

import argparse
import glob
import os

import fragility
import gpdexposure
import intensityprovider
import loss
import shakemap
import tellus


def main():
    """
    Runs the main method, which reads from
    the files,
    updates each exposure cell individually
    and prints out all of the updated exposure cells.
    """
    argparser = argparse.ArgumentParser(
        description="Updates the exposure model and the damage "
        + "classes of the Buildings"
    )
    argparser.add_argument(
        "intensity_file",
        help="File with hazard intensities, for example a shakemap",
    )
    argparser.add_argument("exposure_file", help="File with the exposure data")
    argparser.add_argument(
        "exposure_schema",
        help="The actual schema for the exposure data",
    )
    argparser.add_argument(
        "fragilty_file", help="File with the fragility function data"
    )
    argparser.add_argument(
        "--merged_output_file",
        default="output_merged.json",
        help="Filename for the merged output from all others",
    )
    current_dir = os.path.dirname(os.path.realpath(__file__))
    loss_data_dir = os.path.join(current_dir, "loss_data")
    files = glob.glob(os.path.join(loss_data_dir, "*.json"))

    loss_provider = loss.LossProvider.from_files(files, "USD")

    args = argparser.parse_args()

    intensity_provider = shakemap.Shakemaps.from_file(
        args.intensity_file
    ).to_intensity_provider()
    # add aliases
    # ID for inundation (out of the maximum wave height)
    # SA_01 and SA_03 out of the PGA
    intensity_provider = intensityprovider.AliasIntensityProvider(
        intensity_provider,
        aliases={
            "SA_01": ["PGA"],
            "SA_03": ["PGA"],
            "ID": ["MWH", "INUN_MEAN_POLY"],
        },
    )
    fragility_provider = fragility.Fragility.from_file(
        args.fragilty_file
    ).to_fragility_provider()

    old_exposure = gpdexposure.read_exposure(args.exposure_file)

    worker = tellus.Child(
        intensity_provider,
        fragility_provider,
        old_exposure,
        args.exposure_schema,
        loss_provider,
        args,
    )
    worker.run()


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.set_start_method("spawn")
    main()
