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
Classes for handling of the fragility functions
and the damage states.
"""

import collections
import json
import re

import numpy as np
from scipy.stats import lognorm, norm

FactoryCacheKey = collections.namedtuple("FactoryCacheKey", ["mean", "stddev"])


class LogncdfFactory:
    """
    This is function factory for the log normal cdf.
    """

    def __init__(self):
        self.cache = {}

    def __call__(self, mean, stddev):
        key = FactoryCacheKey(mean, stddev)
        if key in self.cache.keys():
            return self.cache[key]
        # For the parameterization see:
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.lognorm.html
        # "A common parametrization for a lognormal random variable
        # Y is in terms of the mean, mu, and standard deviation, sigma,
        # of the unique normally distributed random variable X such
        # that exp(X) = Y.
        # This parametrization corresponds to setting
        # s = sigma and scale = exp(mu)."
        func = lognorm(scale=np.exp(mean), s=stddev)
        result = CachedFunction(func.cdf)

        self.cache[key] = result
        return result


class NormCdfFactory:
    """This is a function factory for the norm cdf."""

    def __init__(self):
        self.cache = {}

    def __call__(self, mean, stddev):
        key = FactoryCacheKey(mean, stddev)
        if key in self.cache.keys():
            return self.cache[key]
        # See
        # https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.norm.html
        # "The location (loc) keyword specifies the mean.
        # The scale (scale) keyword specifies the standard deviation."
        func = norm(loc=mean, scale=stddev)
        result = CachedFunction(func.cdf)

        self.cache[key] = result
        return result


class CachedFunction:
    """Class to cache function calls."""

    def __init__(self, inner_function):
        """Init the instance with the given function."""
        self.inner_function = inner_function
        self.cache = {}

    def __call__(self, value):
        """Call the function with the value."""
        if value in self.cache.keys():
            return self.cache[value]
        result = self.inner_function(value)
        self.cache[value] = result
        return result


SUPPORTED_FRAGILITY_FUNCTION_FACTORIES = {
    "logncdf": LogncdfFactory(),
    "normcdf": NormCdfFactory(),
}


class DamageState:
    """
    Class to represent the damage states.

    There are some attributes that are not specific for
    damage states as the intensity_field, the intensity_unit,
    the kind of fragility function (lognormcdf for example) or
    the min and max intensities. However in order to work with
    those values more easily, they are included here.
    """

    __slots__ = [
        "taxonomy",
        "from_state",
        "to_state",
        "intensity_field",
        "intensity_unit",
        "fragility_function",
    ]

    def __init__(
        self,
        taxonomy,
        from_state,
        to_state,
        intensity_field,
        intensity_unit,
        fragility_function,
    ):
        self.taxonomy = taxonomy
        self.from_state = from_state
        self.to_state = to_state
        self.intensity_field = intensity_field.upper()
        self.intensity_unit = intensity_unit

        self.fragility_function = fragility_function

    def get_probability_for_intensity(self, intensity, units):
        """
        Returns the probabilit value for the given
        intensity.

        The intensity and units are given as dicts, for example:
        intensity = {
            'PGA': 1.0,
            'STDDEV_PGA': 7.0
        }
        units = {
            'PGA': 'g',
            'STDDEV_PGA': 'g'
        }

        This method throws an exception if the unit for the
        fragility function is not the expected one.
        """
        field = self.intensity_field
        value = intensity[field]
        unit = units[field]

        if unit != self.intensity_unit:
            raise Exception("Not supported unit")

        return self.fragility_function(value)


class Fragility:
    """
    Class to represent all of the fragility data.
    """

    def __init__(self, data):
        self._data = data

    @classmethod
    def from_file(cls, json_file):
        """
        Reads the data from a given json file.
        """
        with open(json_file, "rt") as input_file:
            data = json.load(input_file)
        return cls(data)

    def to_fragility_provider_with_specified_fragility_function(
        self, fragility_function
    ):
        """
        Transforms the data, so that a
        provider for the supported taxonomies
        and the damage states (with the fragility functions)
        are returned.
        """
        damage_states_by_taxonomy = collections.defaultdict(list)

        shape = self._data["meta"]["shape"]

        for dataset in self._data["data"]:
            taxonomy = dataset["taxonomy"]
            intensity_field = dataset["imt"]
            intensity_unit = dataset["imu"]

            for damage_state_mean_key in [
                k
                for k in dataset.keys()
                if k.startswith("D") and k.endswith("_mean")
            ]:
                #
                # the data is in the format
                # D1_mean, D2_mean, D3_mean
                # (as there are is no from data state at the moment)
                # but this code can also handle them the in the way
                # D01, so that it is the damage state from 0 to 1 or
                # D_0_1 or D0_1
                #
                to_state = int(
                    re.search(r"(\d)_mean$", damage_state_mean_key).group(1)
                )
                from_state = int(
                    re.search(r"^D_?(\d)_", damage_state_mean_key).group(1)
                )

                if to_state == from_state:
                    # there is no from state given
                    # both regexp read the same value
                    from_state = 0

                mean = dataset[damage_state_mean_key]
                stddev = dataset[
                    damage_state_mean_key.replace("_mean", "_stddev")
                ]

                damage_state = DamageState(
                    taxonomy=taxonomy,
                    from_state=from_state,
                    to_state=to_state,
                    intensity_field=intensity_field,
                    intensity_unit=intensity_unit,
                    fragility_function=fragility_function(mean, stddev),
                )

                damage_states_by_taxonomy[taxonomy].append(damage_state)
        Fragility._add_damage_states_if_missing(damage_states_by_taxonomy)

        schema = self._data["meta"]["id"]

        return FragilityProvider(damage_states_by_taxonomy, schema)

    def to_fragility_provider(self):
        """
        Transforms the data, so that a
        provider for the supported taxonomies
        and the damage states (with the fragility functions)
        are returned.
        """
        shape = self._data["meta"]["shape"]
        fragility_function = SUPPORTED_FRAGILITY_FUNCTION_FACTORIES[shape]

        return self.to_fragility_provider_with_specified_fragility_function(
            fragility_function
        )

    @staticmethod
    def _add_damage_states_if_missing(damage_states_by_taxonomy):
        """
        Adds missing damage states for example from 1 to 2, 2 to 3, 1 to 3, ...
        if just the 0 to x are given.
        """

        for taxonomy in damage_states_by_taxonomy.keys():
            Fragility._add_damage_states_if_missing_to_dataset_list(
                damage_states_by_taxonomy[taxonomy]
            )

    @staticmethod
    def _add_damage_states_if_missing_to_dataset_list(damage_states):
        """
        If there are data from damage state 0 to 5,
        but none for 1 to 5, than it they should be added.
        """

        max_damage_state = max([ds.to_state for ds in damage_states])
        for from_damage_state in range(0, max_damage_state):
            for to_damage_state in range(1, max_damage_state + 1):
                ds_option = [
                    ds
                    for ds in damage_states
                    if ds.from_state == from_damage_state
                    and ds.to_state == to_damage_state
                ]
                if not ds_option:
                    ds_option_lower = [
                        ds
                        for ds in damage_states
                        if ds.from_state == from_damage_state - 1
                        and ds.to_state == to_damage_state
                    ]
                    if ds_option_lower:
                        ds_lower = ds_option_lower[0]
                        ds_new = DamageState(
                            taxonomy=ds_lower.taxonomy,
                            from_state=ds_lower.from_state + 1,
                            to_state=ds_lower.to_state,
                            intensity_field=ds_lower.intensity_field,
                            intensity_unit=ds_lower.intensity_unit,
                            fragility_function=ds_lower.fragility_function,
                        )
                        damage_states.append(ds_new)


class FragilityProvider:
    """
    Class to give access to the taxonomies and
    the damage states with the fragility functions.
    """

    def __init__(self, damage_states_by_taxonomy, schema):
        self._damage_states_by_taxonomy = damage_states_by_taxonomy
        self.schema = schema

    def get_damage_states_for_taxonomy(self, taxonomy):
        """
        Returns all the damage states for the given
        taxonomy.
        """
        return self._damage_states_by_taxonomy[taxonomy]

    def get_taxonomies(self):
        """
        Returns the taxonomies from the data.
        """
        return self._damage_states_by_taxonomy.keys()
