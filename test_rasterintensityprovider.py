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
Testfile for testing
the intensity provider for rasters.
"""

import collections
import os
import unittest

import rasterintensityprovider


class TestRasterIntensityProvider(unittest.TestCase):
    """
    Test case for accessing the raster via intensity
    provider.
    """

    def test_raster_intensity_provider(self):
        """
        Takes the raster from the testinputs folder.
        Wrapps it into an intensity provider interface.
        Checks the values.
        """
        raster_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "testinputs",
            "fixedDEM_S_VEI_60mio_HYDRO_v10_EROSION_1600_0015_25res"
            + "_4mom_25000s_MaxPressure_smaller.asc",
        )

        intensity = "pressure"
        unit = "p"
        na_value = 0.0
        PointsWithValue = collections.namedtuple(
            "PointsWithValue", "x y value"
        )

        eps = 0.1

        checks = [
            PointsWithValue(x=781687.171, y=9924309.372, value=4344.54),
            PointsWithValue(x=778845.3436538, y=9918842.5687882, value=0),
            PointsWithValue(x=773449.1072520, y=9917890.4097193, value=0),
        ]

        intensity_provider = (
            rasterintensityprovider.RasterIntensityProvider.from_file(
                raster_file, intensity, unit, na_value
            )
        )

        for check in checks:
            intensities, units = intensity_provider.get_nearest(
                lon=check.x, lat=check.y
            )

            self.assertLess(check.value - eps, intensities[intensity])
            self.assertLess(intensities[intensity], check.value + eps)
            self.assertEqual(unit, units[intensity])

    def test_read_tsunami_data(self):
        """Test with our tsunami dataset."""
        raster_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "testinputs",
            "tsunami_peru_mwh.tiff",
        )
        intensity = "MWH"
        unit = "m"
        na_value = 0.0
        intensity_provider = (
            rasterintensityprovider.RasterIntensityProvider.from_file(
                raster_file, intensity, unit, na_value
            )
        )

        PointsWithValue = collections.namedtuple(
            "PointsWithValue", "x y value"
        )

        eps = 0.1
        checks = [
            PointsWithValue(x=-76.986, y=-12.2, value=0.0),
            PointsWithValue(x=-76.8875032300, y=-12.2811898724, value=13.57),
            PointsWithValue(x=-76.913582151, y=-12.261071082, value=4.91),
            # Some that are masked or outside
            # Due to our na_value we should get those back
            PointsWithValue(x=-76.6, y=-12.181, value=0.0),
            PointsWithValue(x=-76.9549164, y=-12.1770012, value=0.0),
            PointsWithValue(x=-76.925, y=-12.185, value=0.0),
        ]
        for check in checks:
            intensities, units = intensity_provider.get_nearest(
                lon=check.x, lat=check.y
            )

            self.assertLess(check.value - eps, intensities[intensity])
            self.assertLess(intensities[intensity], check.value + eps)
            self.assertEqual(unit, units[intensity])


if __name__ == "__main__":
    unittest.main()
