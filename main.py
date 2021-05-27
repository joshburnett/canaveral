from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Union
from time import perf_counter
from tabulate import tabulate
from stringscore import liquidmetal
from copy import deepcopy
import numpy as np
import itertools


@dataclass
class CatalogItem:
    full_path: Path
    name: str
    lower_path: str
    lower_name: str

    def __init__(self, full_path: Path):
        self.full_path = full_path
        self.name = full_path.name
        self.lower_path = str(full_path).lower()
        self.lower_name = self.name.lower()


@dataclass
class MatchDetails:
    catalog_index: int
    match_chars: List[int] = field(default_factory=list)
    match_indices: List[int] = field(default_factory=list)


#%% Score the results
# Scoring methods:
# - Previously selected for given query
# - Consecutive matching letters in name (str.find?)
# - Initial letters of words
# - Non-consecutive matching letters in name
# - Consecutive matching letters in path
# - Non-consecutive matching letters in path

CONSEC_NAME_WEIGHT = 1
INITIAL_LETTERS_NAME_WEIGHT = 1
NONCONSEC_NAME_WEIGHT = 0.5
NONCONSEC_PATH_WEIGHT = 0.25
WORD_SEPARATORS = ' \t_-'


@dataclass
class CatalogItemScore:
    catalog_index: int
    consecutive_name: float = 0
    nonconsecutive_name: float = 0
    nonconsecutive_path: float = 0
    initial_letters_name: float = 0
    liquidmetal: float = 0
    total: float = 0

    def update_total(self):
        self.total = self.consecutive_name*CONSEC_NAME_WEIGHT + \
                     self.nonconsecutive_name*NONCONSEC_NAME_WEIGHT + \
                     self.nonconsecutive_path*NONCONSEC_PATH_WEIGHT + \
                     self.initial_letters_name*INITIAL_LETTERS_NAME_WEIGHT


@dataclass
class SearchPathEntry:
    path: Path
    patterns: List[str] = field(default_factory=lambda: ['*'])
    include_root: bool = False


#%%
def calc_incremental_matches(query_letter):
    # First, go through list of matches for the full path and determine if the characters are in it
    t0 = perf_counter()

    drop_indices = []
    for index in full_path_matches:
        # index = 0
        item = catalog[index]
        match_details = full_path_matches[index]

        # Get the index to start searching
        try:
            start_char = match_details.match_indices[-1]+1
        except IndexError:
            start_char = 0

        try:
            match_details.match_indices.append(item.lower_path[start_char:].index(query_letter) + start_char)
            match_details.match_chars.append(query_letter)
        except ValueError:
            drop_indices.append(index)

    for index in drop_indices:
        del full_path_matches[index]  # can use del since the key is guaranteed to exist

        # If the character isn't in the full path, then they're not going to be in the name alone
        name_nonconsec_matches.pop(index, None)  # using pop because the key may have already been deleted

    full_path_query_times.append(perf_counter() - t0)
    full_path_query_matches.append(deepcopy(full_path_matches))
    query_match_lengths['full path non consecutive'].append(len(full_path_matches))

    # ---------------------------------------------------------------------
    # Now go through the name alone and see if the character is there
    t0 = perf_counter()

    drop_indices = []
    for index in name_nonconsec_matches:
        # index = 0
        item = catalog[index]
        match_details = name_nonconsec_matches[index]
        try:
            start_char = match_details.match_indices[-1]+1
        except IndexError:
            start_char = 0

        try:
            match_details.match_indices.append(item.lower_name[start_char:].index(query_letter) + start_char)
            match_details.match_chars.append(query_letter)
        except ValueError:
            drop_indices.append(index)

    for index in drop_indices:
        del name_nonconsec_matches[index]

    name_nonconsec_query_times.append(perf_counter() - t0)
    name_nonconsec_query_matches.append(deepcopy(name_nonconsec_matches))
    query_match_lengths['name nonconsecutive'].append(len(name_nonconsec_matches))


#%%
search_path_entries = [
    SearchPathEntry(path=Path(r'C:\Users\jburnett1\OneDrive - Werfen\Documents\! Beacon')),
    SearchPathEntry(path=Path(r'C:\Users\jburnett1\code'), patterns=['.dir']),
    SearchPathEntry(
        path=Path(r'C:\Users\jburnett1\AppData\Roaming\Microsoft\Windows\Start Menu\Programs'), patterns=['*.lnk']
    ),
    SearchPathEntry(path=Path(r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs'), patterns=['*.lnk'])
]

#%%
# TODO: add different search options for different root paths (match strings, recursion level)

catalog: List[CatalogItem] = []
for entry in search_path_entries:
    for pattern in entry.patterns:
        if pattern == '.dir':
            # TODO: implement directory handling
            continue
        catalog += [CatalogItem(item_path) for item_path in entry.path.glob(pattern)]

#%%
query = 'edg'


full_path_matches = {index: MatchDetails(catalog_index=index) for index in range(len(catalog))}
name_nonconsec_matches = deepcopy(full_path_matches)

#%
full_path_query_times = []
name_nonconsec_query_times = []
liquidmetal_score_times = []
incremental_score_times = []
query_match_lengths = {'full path non consecutive': [],
                       'name nonconsecutive': [],
                       'name consecutive': [],
                       'name initials': []}

full_path_query_matches = []
name_nonconsec_query_matches = []
liquidmetal_query_scores = []
query_scores = []

result_total_scores = {}
result_catalog_indices = {}
result_full_paths = {}
result_consec_name_scores = {}
result_initial_letter_scores = {}
result_nonconsec_name_scores = {}
result_nonconsec_path_scores = {}
result_liquidmetal_scores = {}


#%
query_so_far = ''
for query_letter in query:
    query_so_far += query_letter
    calc_incremental_matches(query_letter)

    # ---------------------------------------------------------------------
    # Calculate liquidmetal scores
    t0 = perf_counter()
    liquidmetal_scores = [liquidmetal.score(catalog_item.lower_path, query_so_far)
                          for catalog_item in catalog]
    liquidmetal_score_times.append(perf_counter()-t0)

    liquidmetal_query_scores.append(liquidmetal_scores)
    full_paths = [catalog_item.full_path for catalog_item in catalog]

    liquidmetal_score_data = sorted(zip(liquidmetal_scores, full_paths), key=lambda pair: pair[0], reverse=True)
    # print(tabulate(score_data, headers=['Score', 'Full Path'], floatfmt=".2f"))

    t0 = perf_counter()
    scores = {catalog_index: CatalogItemScore(catalog_index=catalog_index) for catalog_index in full_path_matches}
    for index, score in scores.items():
        score.liquidmetal = liquidmetal_scores[index]
    initial_score_creation_time = perf_counter()-t0

    # Calculate incremental scores
    t0 = perf_counter()

    for catalog_index, match in name_nonconsec_matches.items():
        scores[catalog_index].nonconsecutive_name = len(match.match_indices)
        scores[catalog_index].consecutive_name = np.count_nonzero(np.diff(np.array(match.match_indices)) == 1)
        new_word_score = 0
        for char_index in match.match_indices:
            if catalog[catalog_index].lower_name[char_index - 1] in WORD_SEPARATORS:
                new_word_score += 1
        scores[catalog_index].initial_letters_name = new_word_score

    for catalog_index, match in full_path_matches.items():
        scores[catalog_index].nonconsecutive_path = len(match.match_indices)
        scores[catalog_index].update_total()

    sorted_results = sorted([(scores[catalog_index].total, catalog_index, catalog[catalog_index].full_path)
                             for catalog_index in full_path_matches],
                            key=lambda pair: pair[0], reverse=True)

    incremental_scoring_time = perf_counter() - t0
    incremental_score_times.append(incremental_scoring_time)

    query_scores.append(deepcopy(scores))

# print(tabulate(sorted_results, headers=['Score', 'Catalog Index', 'Full Path']))

    result_total_scores[query_so_far] = [result[0] for result in sorted_results]
    result_catalog_indices[query_so_far] = [result[1] for result in sorted_results]
    result_full_paths[query_so_far] = [result[2] for result in sorted_results]
    result_consec_name_scores[query_so_far] = [scores[catalog_index].consecutive_name
                                               for catalog_index in result_catalog_indices[query_so_far]]
    result_initial_letter_scores[query_so_far] = [scores[catalog_index].initial_letters_name
                                                  for catalog_index in result_catalog_indices[query_so_far]]
    result_nonconsec_name_scores[query_so_far] = [scores[catalog_index].nonconsecutive_name
                                                  for catalog_index in result_catalog_indices[query_so_far]]
    result_nonconsec_path_scores[query_so_far] = [scores[catalog_index].nonconsecutive_path
                                                  for catalog_index in result_catalog_indices[query_so_far]]
    result_liquidmetal_scores[query_so_far] = [scores[catalog_index].liquidmetal
                                               for catalog_index in result_catalog_indices[query_so_far]]

    print(f'\n\nQuery so far: {query_so_far}')
    print(f'{len(sorted_results)} matches\n')
    print(tabulate({
        'Total Score': result_total_scores[query_so_far],
        'LiquidMetal Score': result_liquidmetal_scores[query_so_far],
        'Catalog Index': result_catalog_indices[query_so_far],
        'Consecutive Name': result_consec_name_scores[query_so_far],
        'Initial Letter': result_initial_letter_scores[query_so_far],
        'Non-consec Name': result_nonconsec_name_scores[query_so_far],
        'Non-consec Path': result_nonconsec_path_scores[query_so_far],
        'Full Path': result_full_paths[query_so_far],
    }, headers='keys'))


#%%
descriptions = ['Initial index time', 'Initial match creation time'] + \
               list(itertools.chain.from_iterable([[f'Full path query {i + 1}',
                                                    f'Name only query {i + 1}',
                                                    f'Liquidmetal scoring {i + 1}',
                                                    f'Incremental scoring {i + 1}',
                                                    ]
                                                   for i in range(len(full_path_query_times))]))

timing_data = {'Description': descriptions,
               'Time (ms)': [index_time*1000, initial_match_creation_time*1000] +
                            list(itertools.chain.from_iterable(
                                [(a*1000,
                                  b*1000,
                                  c*1000,
                                  d*1000,
                                  )
                                 for a, b, c, d in zip(full_path_query_times,
                                                       name_nonconsec_query_times,
                                                       liquidmetal_score_times,
                                                       incremental_score_times,
                                                       )]))}

# print(tabulate(data, headers={'Description': 'Description', 'time': 'Time (ms)'}, floatfmt=".2f"))
print(tabulate(timing_data, headers='keys', floatfmt=".2f"))


#%% Print matches for full path, non-consecutive
for catalog_index, match in full_path_matches.items():
    str_list = []
    catalog_item = catalog[catalog_index]
    last_match_index = -1
    for index in match.match_indices:
        str_list.extend([catalog_item.lower_path[last_match_index+1:index],
                         f'<{catalog_item.lower_path[index].upper()}>'])
        last_match_index = index
    str_list.append(catalog_item.lower_path[last_match_index+1:])
    print(''.join(str_list))


#%% Print matches for name only, non-consecutive
for catalog_index, match in name_nonconsec_matches.items():
    str_list = []
    catalog_item = catalog[catalog_index]
    last_match_index = -1
    for index in match.match_indices:
        str_list.extend([catalog_item.lower_name[last_match_index+1:index],
                         f'<{catalog_item.lower_name[index].upper()}>'])
        last_match_index = index
    str_list.append(catalog_item.lower_name[last_match_index+1:])
    print(''.join(str_list))

