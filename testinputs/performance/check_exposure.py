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

import collections
import pandas
import geopandas

TaxDsTuple = collections.namedtuple("TaxDsTuple", "taxonomy damage state")

all_cells = geopandas.read_file("exposure_so_far.json")

all_expos = all_cells["expo"]

for expo in all_expos:
    expo_df = pandas.DataFrame(expo)
    tax_ds_tuples_counts = collections.defaultdict(lambda: 0)

    for _, row in expo_df.iterrows():
        taxonomy = row["Taxonomy"]
        ds = row["Damage"]

        tax_ds_tuples_counts[TaxDsTuple(taxonomy, ds)] += 1

    any_more_than_1 = any([v > 1 for v in tax_ds_tuples_counts.values()])
    assert any_more_than_1 is False
