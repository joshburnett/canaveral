from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from fnmatch import fnmatch
from copy import deepcopy

import numpy as np
from tabulate import tabulate
from stringscore import liquidmetal
import yaml

import prettyprinter

from typing import List, Optional, Dict, Tuple, Union


prettyprinter.install_extras(include=('dataclasses',))


#%% Scoring methods & weights:
# - Most recently selected for given query
# ? Current query is initial substring of a query for which this was the most recently selected
# - Consecutive matching letters in name
# - Initial letters of words
# - Non-consecutive matching letters in name
# ? Consecutive matching letters in path
# - Non-consecutive matching letters in path

LATEST_MATCH_WEIGHT = 5
PREVIOUSLY_LAUNCHED_WEIGHT = 2
CONSEC_NAME_WEIGHT = 1.2
INITIAL_LETTERS_NAME_WEIGHT = 1
NONCONSEC_NAME_WEIGHT = 0.5
NONCONSEC_PATH_WEIGHT = 0.25
WORD_SEPARATORS = ' \t_-'


#%%
def deep_glob(path: Path, depth: int = 0, pattern: str = '*', include_dotdirs=False):
    # Negative values for depth will descend into all subdirectories
    try:
        for child in path.iterdir():
            if child.is_dir():
                if include_dotdirs or fnmatch(child.name, '[!.]*'):
                    yield child
                    if depth != 0:
                        yield from deep_glob(path=child, depth=depth - 1, pattern=pattern)
            elif fnmatch(child.name, pattern):
                yield child
    except PermissionError:
        pass


def findall(string, char, start=0):
    return [i+start for i, c in enumerate(string[start:]) if c == char]


@dataclass(frozen=True)  # needs to be frozen so we can hash it to create a set of these
class CatalogItem:
    full_path: Path
    name: Optional[str] = field(repr=False, default=None)
    lower_name: Optional[str] = field(repr=False, default=None)

    def __post_init__(self):
        object.__setattr__(self, 'name', self.full_path.name)
        object.__setattr__(self, 'lower_name', self.full_path.name.lower())


@dataclass
class SearchPathEntry:
    path: Union[Path, str]
    patterns: List[str] = field(default_factory=lambda: ['*'])
    include_root: bool = False
    search_depth: int = 0

    def __post_init__(self):
        self.path = Path(self.path)


@dataclass
class Catalog:
    items: List[CatalogItem]
    queries: dict[str, Query]
    search_paths: List[SearchPathEntry]
    launch_choices: dict[str, Path]  # dict where keys are the abbreviations that were typed,
                                     # and the values are the resulting paths that were launched
    recent_launches: List[Path]  # list of all the recent items that were launched, ordered recent to oldest
    recent_launch_list_limit: int
    launch_data_file: Path

    def __init__(self, search_paths: List[SearchPathEntry], launch_data_file: Path,
                 recent_launch_list_limit: int = 50):
        self.items = []
        self.search_paths = search_paths
        self._create_items_list(search_paths)
        self.queries = {}
        self.recent_launch_list_limit = recent_launch_list_limit
        self.recent_launches = []
        self.launch_choices = {}
        self.launch_data_file = launch_data_file
        self.load_launch_data_from_file()

    def load_launch_data_from_file(self) -> None:
        if self.launch_data_file.exists():
            with open(self.launch_data_file, 'r') as file:
                launch_data = yaml.safe_load(file)
            self.launch_choices = {q: Path(pathstr) for q, pathstr in launch_data['launch choices'].items()}
            self.recent_launches = [Path(pathstr) for pathstr in launch_data['recent launches']]

    def update_launch_data(self, query_string: str, launch_choice: Path) -> None:
        self.launch_choices[query_string] = launch_choice
        try:
            old_index = self.recent_launches.index(launch_choice)
            self.recent_launches.pop(old_index)
        except ValueError:  # item wasn't in list
            pass

        self.recent_launches.insert(0, launch_choice)
        while len(self.recent_launches) > self.recent_launch_list_limit:
            self.recent_launches.pop()

        data = {
            'launch choices': {q: str(choice) for q, choice in self.launch_choices.items()},
            'recent launches': [str(launch_path) for launch_path in self.recent_launches]
        }
        with open(self.launch_data_file, 'w') as file:
            yaml.dump(data, file, width=1000)

    def _create_items_list(self, search_paths: List[SearchPathEntry]) -> None:
        items = []
        self.queries = {}
        self.search_paths = search_paths

        for search_path in search_paths:
            expanded_path = search_path.path.expanduser()
            if search_path.include_root:
                items.append(CatalogItem(expanded_path))
            for pattern in search_path.patterns:
                if pattern == '.dir':
                    items += [CatalogItem(item_path)
                              for item_path in deep_glob(expanded_path,
                                                         depth=search_path.search_depth, pattern='[!.]*')
                              if item_path.is_dir()]
                else:
                    items += [CatalogItem(item_path)
                              for item_path in deep_glob(expanded_path,
                                                         depth=search_path.search_depth, pattern=pattern)]

        self.items = list(set(items))

    def query(self, query_text: str):
        if query_text not in self.queries:
            if len(query_text) > 1:
                self.query(query_text[:-1])
                self.queries[query_text] = Query(catalog=self, parent=self.queries[query_text[:-1]], query=query_text)
            else:
                self.queries[query_text] = Query(catalog=self, parent=self, query=query_text)

        return self.queries[query_text]


@dataclass
class Query:
    query_text: str
    matches: List[Match] = field(repr=False)
    sorted_score_results: Optional[Tuple[ScoreResult]] = field(default=None, repr=False)

    def __init__(self, catalog: Catalog, parent: Union[Catalog, Query], query: str):
        if type(parent) is Catalog:
            self.query_text = query[0]
            self.matches = [Match(catalog_item=item,
                                  catalog=catalog,
                                  match_chars=query[0],
                                  match_indices=[i])
                            for item in parent.items
                            for i in findall(item.lower_name, query[0])]

        elif type(parent) is Query:
            self.query_text = query[:len(parent.query_text) + 1]
            query_len = len(self.query_text)

            self.matches = [Match(catalog_item=match.catalog_item,
                                  catalog=catalog,
                                  match_chars=query[:query_len],
                                  match_indices=match.match_indices + [i])
                            for match in parent.matches
                            for i in findall(match.catalog_item.lower_name,
                                             query[query_len-1],
                                             match.match_indices[-1]+1)]

        else:
            raise TypeError('Query parent must be either a Catalog or another Query object')

        score_results = {}
        for match in self.matches:
            if match.catalog_item.full_path not in score_results or \
                    match.score.result > score_results[match.catalog_item.full_path].total_score:
                score_results[match.catalog_item.full_path] = ScoreResult(item=match.catalog_item,
                                                                          match=match,
                                                                          total_score=match.score.result)

            # score_result = score_results.get(match.catalog_item.full_path,
            #                                  ScoreResult(item=match.catalog_item, total_score=0))
            # score_result.total_score += match.score.result
            # score_results[match.catalog_item.full_path] = score_result

        self.sorted_score_results = tuple(sorted(score_results.values(),
                                                 key=lambda result: result.total_score, reverse=True))

    def print_scores(self):
        # scores = self.score_set
        total_scores = [result.total_score for result in self.sorted_score_results]
        catalog_indices = [result.catalog_index for result in self.sorted_score_results]
        full_paths = [result.item.full_path for result in self.sorted_score_results]
        item_names = [result.item.full_path.name for result in self.sorted_score_results]
        liquidmetal_name_scores = [result.match.score.liquidmetal_name for result in self.sorted_score_results]
        # liquidmetal_name_scores = [scores[catalog_index].liquidmetal_name
        #                            for catalog_index in catalog_indices]

        print(f'\n\nQuery: {self.query_text}')
        print(f'{len(self.sorted_score_results)} matches\n')
        print(tabulate({
            'Total Score': total_scores,
            'LiquidMetal Name Score': liquidmetal_name_scores,
            # 'Catalog Index': catalog_indices,
            'Item Name': item_names,
            'Full Path': full_paths,
        }, headers='keys'))

    def print_detailed_scores(self):
        # scores = self.score_set
        total_scores = [result.total_score for result in self.sorted_score_results]
        catalog_indices = [result.catalog_index for result in self.sorted_score_results]
        item_names = [result.item.full_path.name for result in self.sorted_score_results]
        full_paths = [result.item.full_path for result in self.sorted_score_results]
        consec_name_scores = [result.match.score.consecutive_name for result in self.sorted_score_results]
        initial_letter_scores = [result.match.score.initial_letters_name for result in self.sorted_score_results]
        nonconsec_name_scores = [result.match.score.nonconsecutive_name for result in self.sorted_score_results]
        liquidmetal_name_scores = [result.match.score.liquidmetal_name for result in self.sorted_score_results]
        last_choice_scores = [result.match.score.is_latest_match for result in self.sorted_score_results]
        recent_launch_scores = [result.match.score.previously_launched for result in self.sorted_score_results]

        # consec_name_scores = [scores[catalog_index].consecutive_name
        #                       for catalog_index in catalog_indices]
        # initial_letter_scores = [scores[catalog_index].initial_letters_name
        #                          for catalog_index in catalog_indices]
        # nonconsec_name_scores = [scores[catalog_index].nonconsecutive_name
        #                          for catalog_index in catalog_indices]
        # liquidmetal_name_scores = [scores[catalog_index].liquidmetal_name
        #                            for catalog_index in catalog_indices]

        print(f'\n\nQuery: {self.query_text}')
        print(f'{len(self.sorted_score_results)} matches\n')
        print(tabulate({
            'Total Score': total_scores,
            'LiquidMetal Name Score': liquidmetal_name_scores,
            'Item Name': item_names,
            'Last match': last_choice_scores,
            'Recent': recent_launch_scores,
            # 'Catalog Index': catalog_indices,
            'Consecutive Name': consec_name_scores,
            'Initial Letter': initial_letter_scores,
            'Non-consec Name': nonconsec_name_scores,
            'Full Path': full_paths,
        }, headers='keys'))


@dataclass
class Match:
    catalog_item: CatalogItem
    catalog: Catalog
    match_chars: str = field(default_factory=str)
    match_indices: List[int] = field(default_factory=list)
    score: Optional[Score] = None

    def __post_init__(self):
        new_word_score = 0
        for char_index in self.match_indices:
            if self.catalog_item.name[char_index - 1] in WORD_SEPARATORS:
                new_word_score += 1

        self.score = Score(catalog_item=self.catalog_item,
                           is_latest_match=self.catalog.launch_choices.get(self.match_chars, None) == self.catalog_item.full_path,
                           previously_launched=self.catalog_item.full_path in self.catalog.recent_launches,
                           liquidmetal_name=liquidmetal.score(self.catalog_item.lower_name, self.match_chars),
                           nonconsecutive_name=len(self.match_indices),
                           consecutive_name=sum([1 if y-x == 1 else 0 for x, y in
                                                 zip(self.match_indices[:-1], self.match_indices[1:])]),
                           initial_letters_name=new_word_score)
        # self.score.consecutive_name = np.count_nonzero(np.diff(np.array(self.match_indices)) == 1)


#%%
@dataclass
class Score:
    catalog_item: CatalogItem
    is_latest_match: bool = False
    previously_launched: bool = False
    consecutive_name: float = 0
    liquidmetal_name: float = 0
    nonconsecutive_name: float = 0
    initial_letters_name: float = 0
    result: float = 0

    def __post_init__(self):
        self.update_total()

    def update_total(self):
        self.result = self.consecutive_name * CONSEC_NAME_WEIGHT + \
                      self.nonconsecutive_name * NONCONSEC_NAME_WEIGHT + \
                      self.initial_letters_name * INITIAL_LETTERS_NAME_WEIGHT + \
                      self.is_latest_match * LATEST_MATCH_WEIGHT + \
                      self.previously_launched * PREVIOUSLY_LAUNCHED_WEIGHT


@dataclass
class ScoreResult:
    item: CatalogItem
    match: Match
    total_score: float
    catalog_index: Optional[int] = None

    def __post_init__(self):
        self.total_score = self.match.score.result


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
class OldQuery:
    new_char: str
    query_so_far: str
    catalog: Catalog = field(repr=False)
    score_set: Dict[int: Score] = field(repr=False)
    match_details_set_names: Dict[int: MatchDetails] = field(repr=False)
    # sorted_items: List[CatalogItem] = field(default_factory=list)
    sorted_score_results: Optional[Tuple[ScoreResult]] = None

    def __init__(self, new_char: str, old_query: Optional[OldQuery] = None, catalog: Optional[Catalog] = None):
        self.new_char = new_char
        if old_query is None:
            self.query_so_far = self.new_char
            if catalog is None:
                raise RuntimeError('Must specify either old_query or catalog when creating a new Query object')
            self.catalog = catalog
            self.match_details_set_names = {catalog_index: MatchDetails(text=catalog.items[catalog_index].lower_name)
                                            for catalog_index in range(len(catalog.items))}
        else:
            self.query_so_far = old_query.query_so_far + new_char
            self.catalog = old_query.catalog
            self.match_details_set_names = deepcopy(old_query.match_details_set_names)

        self.score_set = {catalog_index: Score() for catalog_index in self.match_details_set_names}

        self._update_matches()
        self._update_scores()

    def _update_matches(self):
        # Check list of name matches for new character
        drop_indices = []
        for catalog_index, match_details in self.match_details_set_names.items():
            result = match_details.update_with_new_char(self.new_char)
            if not result:
                drop_indices.append(catalog_index)

        for catalog_index in drop_indices:
            # Can use del since the key is guaranteed to exist (faster than .pop()).
            del self.match_details_set_names[catalog_index]
            # self.match_details_set_names.pop(catalog_index, None)

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
            score_set[catalog_index].update_total()

        self.sorted_score_results = tuple(sorted([ScoreResult(item=self.catalog.items[catalog_index],
                                                              total_score=self.score_set[catalog_index].result,
                                                              catalog_index=catalog_index)
                                                  for catalog_index in self.match_details_set_names],
                                                 key=lambda result: result.total_score, reverse=True))

    # @property
    # def sorted_scores(self):
    #     return sorted([(self.score_set[catalog_index].result, catalog_index,
    #                     self.catalog.items[catalog_index].full_path)
    #                    for catalog_index in self.match_details_set_paths],
    #                   key=lambda item: item[0], reverse=True)

    def print_matched_name_chars(self):
        for match in self.match_details_set_names.values():
            match.print_matched_chars()

    def print_scores(self):
        scores = self.score_set
        total_scores = [result.total_score for result in self.sorted_score_results]
        catalog_indices = [result.catalog_index for result in self.sorted_score_results]
        full_paths = [result.item.full_path for result in self.sorted_score_results]
        liquidmetal_name_scores = [scores[catalog_index].liquidmetal_name
                                   for catalog_index in catalog_indices]

        print(f'\n\nQuery: {self.query_so_far}')
        print(f'{len(self.sorted_score_results)} matches\n')
        print(tabulate({
            'Total Score': total_scores,
            'LiquidMetal Name Score': liquidmetal_name_scores,
            'Catalog Index': catalog_indices,
            'Full Path': full_paths,
        }, headers='keys'))

    def print_detailed_scores(self):
        scores = self.score_set
        total_scores = [result.total_score for result in self.sorted_score_results]
        catalog_indices = [result.catalog_index for result in self.sorted_score_results]
        full_paths = [result.item.full_path for result in self.sorted_score_results]
        consec_name_scores = [scores[catalog_index].consecutive_name
                              for catalog_index in catalog_indices]
        initial_letter_scores = [scores[catalog_index].initial_letters_name
                                 for catalog_index in catalog_indices]
        nonconsec_name_scores = [scores[catalog_index].nonconsecutive_name
                                 for catalog_index in catalog_indices]
        liquidmetal_name_scores = [scores[catalog_index].liquidmetal_name
                                   for catalog_index in catalog_indices]

        print(f'\n\nQuery: {self.query_so_far}')
        print(f'{len(self.sorted_score_results)} matches\n')
        print(tabulate({
            'Total Score': total_scores,
            'LiquidMetal Name Score': liquidmetal_name_scores,
            'Catalog Index': catalog_indices,
            'Consecutive Name': consec_name_scores,
            'Initial Letter': initial_letter_scores,
            'Non-consec Name': nonconsec_name_scores,
            'Full Path': full_paths,
        }, headers='keys'))


@dataclass
class QuerySet:
    catalog: Catalog
    queries: Dict[str: OldQuery] = field(default_factory=dict)

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
                self.queries[query_string] = OldQuery(new_char=query_string, catalog=self.catalog)
            else:
                sub_query = self.create_query(query_string=query_string[:-1])
                self.queries[query_string] = OldQuery(new_char=query_string[-1], old_query=sub_query)

        return self.queries[query_string]
