from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from copy import deepcopy

from stringscore import liquidmetal
from tabulate import tabulate
import numpy as np

from typing import List, Optional, Dict



#%% Scoring methods & weights:
# - Most recently selected for given query
# ? Current query is initial substring of a query for which this was the most recently selected
# - Consecutive matching letters in name
# - Initial letters of words
# - Non-consecutive matching letters in name
# ? Consecutive matching letters in path
# - Non-consecutive matching letters in path

CONSEC_NAME_WEIGHT = 1
INITIAL_LETTERS_NAME_WEIGHT = 1
NONCONSEC_NAME_WEIGHT = 0.5
NONCONSEC_PATH_WEIGHT = 0.25
WORD_SEPARATORS = ' \t_-'


#%%
@dataclass
class CatalogItem:
    full_path: Path
    name: str = field(repr=False)
    lower_path: str = field(repr=False)
    lower_name: str = field(repr=False)

    def __init__(self, full_path: Path):
        self.full_path = full_path
        self.name = full_path.name
        self.lower_path = str(full_path).lower()
        self.lower_name = self.name.lower()


@dataclass
class SearchPathEntry:
    path: Path
    patterns: List[str] = field(default_factory=lambda: ['*'])
    include_root: bool = False
    search_depth: int = 0


# TODO: Add search options: recursion level (from -1), include root
@dataclass
class Catalog:
    items: List[CatalogItem]

    def __init__(self, search_paths: List[SearchPathEntry]):
        self.items = []
        for entry in search_paths:
            for pattern in entry.patterns:
                if pattern == '.dir':
                    # TODO: implement directory handling
                    continue
                self.items += [CatalogItem(item_path) for item_path in entry.path.glob(pattern)]


@dataclass
class Score:
    consecutive_name: float = 0
    liquidmetal_path: float = 0
    liquidmetal_name: float = 0
    nonconsecutive_name: float = 0
    nonconsecutive_path: float = 0
    initial_letters_name: float = 0
    result: float = 0

    def update_total(self):
        self.result = self.consecutive_name * CONSEC_NAME_WEIGHT + \
                      self.nonconsecutive_name * NONCONSEC_NAME_WEIGHT + \
                      self.nonconsecutive_path * NONCONSEC_PATH_WEIGHT + \
                      self.initial_letters_name * INITIAL_LETTERS_NAME_WEIGHT


@dataclass
class MatchDetails:
    text: str
    match_chars: List[str] = field(default_factory=list)
    match_indices: List[int] = field(default_factory=list)

    def update_with_new_char(self, new_char):
        # TODO: Check for match. Return new MatchDetails object w/ updated query info if match, otherwise return None.
        # Get the index to start searching
        try:
            start_char = self.match_indices[-1]+1
        except IndexError:
            start_char = 0

        try:
            self.match_indices.append(self.text[start_char:].index(new_char) + start_char)
            self.match_chars.append(new_char)
        except ValueError:
            return False

        return True

    @property
    def matched_chars(self):
        str_list = []
        last_match_index = -1
        for index in self.match_indices:
            str_list.extend([self.text[last_match_index + 1:index],
                             f'<{self.text[index].upper()}>'])
            last_match_index = index
        str_list.append(self.text[last_match_index + 1:])
        return ''.join(str_list)

    def print_matched_chars(self):
        print(self.matched_chars)


@dataclass
class Query:
    new_char: str
    query_so_far: str
    catalog: Catalog = field(repr=False)
    score_set: Dict[int: Score] = field(repr=False)
    match_details_set_paths: Dict[int: MatchDetails] = field(repr=False)
    match_details_set_names: Dict[int: MatchDetails] = field(repr=False)

    def __init__(self, new_char: str, old_query: Optional[Query] = None, catalog: Optional[Catalog] = None):
        self.new_char = new_char
        if old_query is None:
            self.query_so_far = self.new_char
            if catalog is None:
                raise RuntimeError('Must specify either old_query or catalog when creating a new Query object')
            self.catalog = catalog
            self.match_details_set_paths = {catalog_index: MatchDetails(text=catalog.items[catalog_index].lower_path)
                                            for catalog_index in range(len(catalog.items))}
            self.match_details_set_names = {catalog_index: MatchDetails(text=catalog.items[catalog_index].lower_name)
                                            for catalog_index in range(len(catalog.items))}
        else:
            self.query_so_far = old_query.query_so_far + new_char
            self.catalog = old_query.catalog
            self.match_details_set_paths = deepcopy(old_query.match_details_set_paths)
            self.match_details_set_names = deepcopy(old_query.match_details_set_names)

        self.score_set = {catalog_index: Score() for catalog_index in self.match_details_set_paths}

        self._update_matches()
        self._update_scores()

    def _update_matches(self):
        # First check dict of full path matches for new character
        #   Store new match data when new char is found
        #   Prune full path and name dicts if not found
        # Check list of name matches for new character
        #   Store new match data when new char is found
        #   Prune name dict if not found

        # First check dict of full path matches for new character
        drop_indices = []
        for catalog_index, match_details in self.match_details_set_paths.items():
            if not match_details.update_with_new_char(self.new_char):
                drop_indices.append(catalog_index)

        for catalog_index in drop_indices:
            # Can use del since the key is guaranteed to exist (faster than .pop()).
            del self.match_details_set_paths[catalog_index]

            # If the character isn't in the full path, then it won't be in the name alone either.
            #   (Using .pop() because the key may have already been deleted earlier.)
            self.match_details_set_names.pop(catalog_index, None)

        # Then check list of name matches for new character
        drop_indices = []
        for catalog_index, match_details in self.match_details_set_names.items():
            result = match_details.update_with_new_char(self.new_char)
            if not result:
                drop_indices.append(catalog_index)

        for catalog_index in drop_indices:
            # As with above, using .pop() because the key may have already been deleted earlier.
            self.match_details_set_names.pop(catalog_index, None)

    def _update_scores(self):
        score_set = self.score_set
        query_so_far = self.query_so_far

        for catalog_index, match in self.match_details_set_names.items():
            score = score_set[catalog_index]
            score.liquidmetal_name = liquidmetal.score(match.text, query_so_far)
            score.nonconsecutive_name = len(match.match_indices)
            score.consecutive_name = np.count_nonzero(np.diff(np.array(match.match_indices)) == 1)
            new_word_score = 0
            for char_index in match.match_indices:
                if match.text[char_index - 1] in WORD_SEPARATORS:
                    new_word_score += 1
            score.initial_letters_name = new_word_score

        for catalog_index, match in self.match_details_set_paths.items():
            score_set[catalog_index].liquidmetal_path = liquidmetal.score(match.text, query_so_far)
            score_set[catalog_index].nonconsecutive_path = len(match.match_indices)
            score_set[catalog_index].update_total()

    @property
    def sorted_scores(self):
        return sorted([(self.score_set[catalog_index].result, catalog_index,
                        self.catalog.items[catalog_index].full_path)
                       for catalog_index in self.match_details_set_paths],
                      key=lambda item: item[0], reverse=True)

    def print_matched_name_chars(self):
        for match in self.match_details_set_names.values():
            match.print_matched_chars()

    def print_matched_path_chars(self):
        for match in self.match_details_set_paths.values():
            match.print_matched_chars()

    def print_scores(self):
        scores = self.score_set
        sorted_scores = self.sorted_scores
        total_scores = [result[0] for result in sorted_scores]
        catalog_indices = [result[1] for result in sorted_scores]
        full_paths = [result[2] for result in sorted_scores]
        liquidmetal_path_scores = [scores[catalog_index].liquidmetal_path
                                   for catalog_index in catalog_indices]
        liquidmetal_name_scores = [scores[catalog_index].liquidmetal_name
                                   for catalog_index in catalog_indices]

        print(f'\n\nQuery: {self.query_so_far}')
        print(f'{len(sorted_scores)} matches\n')
        print(tabulate({
            'Total Score': total_scores,
            'LiquidMetal Path Score': liquidmetal_path_scores,
            'LiquidMetal Name Score': liquidmetal_name_scores,
            'Catalog Index': catalog_indices,
            'Full Path': full_paths,
        }, headers='keys'))

    def print_detailed_scores(self):
        scores = self.score_set
        sorted_scores = self.sorted_scores
        total_scores = [result[0] for result in sorted_scores]
        catalog_indices = [result[1] for result in sorted_scores]
        full_paths = [result[2] for result in sorted_scores]
        consec_name_scores = [scores[catalog_index].consecutive_name
                              for catalog_index in catalog_indices]
        initial_letter_scores = [scores[catalog_index].initial_letters_name
                                 for catalog_index in catalog_indices]
        nonconsec_name_scores = [scores[catalog_index].nonconsecutive_name
                                 for catalog_index in catalog_indices]
        nonconsec_path_scores = [scores[catalog_index].nonconsecutive_path
                                 for catalog_index in catalog_indices]
        liquidmetal_path_scores = [scores[catalog_index].liquidmetal_path
                                   for catalog_index in catalog_indices]
        liquidmetal_name_scores = [scores[catalog_index].liquidmetal_name
                                   for catalog_index in catalog_indices]

        print(f'\n\nQuery: {self.query_so_far}')
        print(f'{len(sorted_scores)} matches\n')
        print(tabulate({
            'Total Score': total_scores,
            'LiquidMetal Path Score': liquidmetal_path_scores,
            'LiquidMetal Name Score': liquidmetal_name_scores,
            'Catalog Index': catalog_indices,
            'Consecutive Name': consec_name_scores,
            'Initial Letter': initial_letter_scores,
            'Non-consec Name': nonconsec_name_scores,
            'Non-consec Path': nonconsec_path_scores,
            'Full Path': full_paths,
        }, headers='keys'))


@dataclass
class QuerySet:
    catalog: Catalog
    queries: Dict[str: Query] = field(default_factory=dict)

    def create_query(self, query_string):
        # Cases:
        # - Same as existing query
        #   - Look up & return existing query
        # - New single-letter query
        #   - Start a new query, store & return it
        # - At least partially based on an old query
        #   Naive implementation
        #   - Take a letter off the end and recurse in until either a base query is found or at an empty query string
        #       - Return the base query if found
        #       - If at an empty string, start a new one
        #   - Return the base query and build up one letter at a time until we reach the
        if query_string not in self.queries:
            if len(query_string) == 1:
                self.queries[query_string] = Query(new_char=query_string, catalog=self.catalog)
            else:
                sub_query = self.create_query(query_string=query_string[:-1])
                self.queries[query_string] = Query(new_char=query_string[-1], old_query=sub_query)

        return self.queries[query_string]
