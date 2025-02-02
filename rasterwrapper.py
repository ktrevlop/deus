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

"""This is a module to provide wrappers for raster data."""


class RasterWrapper:
    """
    This is a wrapper using the rasterio
    api to get on the data.
    """

    def __init__(self, raster_reader):
        self._raster_reader = raster_reader
        self._data = raster_reader.read()

    def is_location_in_bbox(self, lon, lat):
        """
        Tests if a location is in the bounding box of the
        raster.
        """
        bbox = self._raster_reader.bounds
        if lon < bbox.left:
            return False
        if lon > bbox.right:
            return False
        if lat < bbox.bottom:
            return False
        if lat > bbox.top:
            return False

        return True

    def get_sample(self, lon, lat):
        """
        Returns the value at the given location.
        Please note: This function does not test if
        the location is in the bounding box of the data.
        Please check that before you query the values!.
        """
        idx = self._raster_reader.index(lon, lat)
        # at the moment it only supports one band
        return self._data[0, idx[0], idx[1]]
