from __future__ import annotations

import sys
import os
from dataclasses import dataclass, field
from pathlib import Path
from fnmatch import fnmatch
import string

import winpath
from tabulate import tabulate
import yaml
from loguru import logger

if Path(sys.executable).stem != 'pythonw':
    import prettyprinter
    prettyprinter.install_extras(include=('dataclasses',))


#%% Scoring methods & weights:
# - Most recently selected for given query
# ? Current query is initial substring of a query for which this was the most recently selected
# ? This item was previously/recently launched
# - Consecutive matching letters in name
# - Initial letters of words
# - Non-consecutive matching letters in name
# ? Consecutive matching letters in path
# - Non-consecutive matching letters in path

LATEST_MATCH_WEIGHT = 5
PREVIOUSLY_LAUNCHED_WEIGHT = 4
CONSEC_NAME_WEIGHT = 2
INITIAL_LETTERS_NAME_WEIGHT = 1.5
NONCONSEC_NAME_WEIGHT = 0.5
NONCONSEC_PATH_WEIGHT = 0.25
WORD_SEPARATORS = ' \t_-'


#%%
def deep_glob(path: Path | os.DirEntry, depth: int = 0, patterns: list[str] = ('*',),
              include_dirs=False, exclude_dotdirs=True, search_dotdirs=False):
    # Negative values for depth will descend into all subdirectories
    try:
        for child in os.scandir(path):
            if child.is_dir():
                is_not_dotdir = fnmatch(child.name, '[!.]*')
                if include_dirs and (not exclude_dotdirs or is_not_dotdir):
                    yield child
                if depth != 0 and (search_dotdirs or is_not_dotdir):
                    yield from deep_glob(path=child.path, depth=depth - 1, patterns=patterns,
                                         include_dirs=include_dirs, exclude_dotdirs=exclude_dotdirs,
                                         search_dotdirs=search_dotdirs)
            else:
                name = child.name
                for pattern in patterns:
                    if fnmatch(name, pattern):
                        yield child
    except PermissionError:
        pass


def findall(string, char, start=0):
    return [i+start for i, c in enumerate(string[start:]) if c == char]


@dataclass(frozen=True)  # needs to be frozen so we can hash it to create a set of these
class CatalogItem:
    """
    Represents an item in a catalog. Initialized w/ the full path of an item and constructs the name and
    lower-case name from this.
    """
    full_path: Path
    name: str | None = field(repr=False, default=None)
    lower_name: str | None = field(repr=False, default=None)

    def __repr__(self):
        return f"CatalogItem(full_path='{self.full_path}')"

    def __post_init__(self):
        object.__setattr__(self, 'name', self.full_path.name)
        object.__setattr__(self, 'lower_name', self.full_path.name.lower())


@dataclass
class SearchPathEntry:
    """Represents a location that should be indexed, along with parameters that control what to index"""
    path: str  # can be a shortcut abbreviation or a regular string
    full_path: Path = None  # no need to specify, as it gets created from path
    patterns: list[str] = field(default_factory=lambda: ['*'])
    include_root: bool = False
    include_dirs: bool = False
    exclude_dotdirs: bool = True
    search_dotdirs: bool = False
    search_depth: int = 0

    def __post_init__(self):
        match self.path:
            case '$user_docs':
                self.full_path = Path(winpath.get_my_documents())
            case '$user_start_menu':
                self.full_path = Path(winpath.get_programs())
            case _:
                self.full_path = Path(self.path).expanduser()


# @dataclass
class Catalog:
    """
    Stores the file index, along with the queries that have been executed (and their results), the paths
    being searched, the record of what the user has chosen to launch from past queries, the list of
    recently-launched items in the index, and the location of a file that stores the user's choices
    """
    items: list[CatalogItem]
    queries: dict[str, Query]
    search_paths: list[SearchPathEntry]
    launch_choices: dict[str, Path]  # dict where keys are the abbreviations that were typed,
                                     # and the values are the resulting paths that were launched
    recent_launches: list[Path]  # list of all the recent items that were launched, ordered recent to oldest
    recent_launch_list_limit: int
    launch_data_file: Path

    def __init__(self, search_paths: list[SearchPathEntry], launch_data_file: Path | None = None,
                 recent_launch_list_limit: int = 50):
        self.items = []
        self.search_paths = search_paths
        self.queries = {}
        self.recent_launch_list_limit = recent_launch_list_limit
        self.recent_launches = []
        self.launch_choices = {}
        self.launch_data_file = launch_data_file
        self.load_launch_data_from_file()
        self.refresh_items_list()

    def __repr__(self):
        return f'Catalog: {len(self.items)} items, {len(self.search_paths)} search paths, ' \
               f'{len(self.queries)} queries'

    def load_launch_data_from_file(self) -> None:
        if self.launch_data_file is not None and self.launch_data_file.exists():
            with open(self.launch_data_file, 'r') as file:
                launch_data = yaml.safe_load(file)
            self.launch_choices = {q: Path(pathstr) for q, pathstr in launch_data['launch choices'].items()}
            self.recent_launches = [Path(pathstr) for pathstr in launch_data['recent launches']]

    def update_launch_data(self, query_string: str, new_launch_choice: Path) -> None:
        old_launch_choice = self.launch_choices.get(query_string, None)
        self.launch_choices[query_string] = new_launch_choice
        try:
            old_index = self.recent_launches.index(new_launch_choice)
            self.recent_launches.pop(old_index)
        except ValueError:  # item wasn't in list
            pass

        self.recent_launches.insert(0, new_launch_choice)
        while len(self.recent_launches) > self.recent_launch_list_limit:
            self.recent_launches.pop()

        data = {
            'launch choices': {q: str(choice) for q, choice in self.launch_choices.items()},
            'recent launches': [str(launch_path) for launch_path in self.recent_launches]
        }
        with open(self.launch_data_file, 'w') as file:
            yaml.dump(data, file, width=1000)

        if old_launch_choice == new_launch_choice:
            logger.info(f'Updating scores for {new_launch_choice.name}')
        else:
            logger.info(f'Updating scores for new: {new_launch_choice.name}, old: {old_launch_choice.name}')

        updates = 0
        for query in self.queries.values():
            if old_launch_choice != new_launch_choice:
                query.update_match_score_if_relevant(old_launch_choice)
                updates += 1
            query.update_match_score_if_relevant(new_launch_choice)
            updates += 1
        logger.info(f'{updates} updates completed')

    def refresh_items_list(self) -> None:
        logger.debug('Refreshing catalog items list')
        items = []
        self.queries = {}

        for search_path in self.search_paths:
            expanded_path = search_path.full_path.expanduser()
            if search_path.include_root:
                items.append(CatalogItem(expanded_path))

            items += [CatalogItem(Path(dir_entry.path))
                      for dir_entry in deep_glob(expanded_path,
                                                 depth=search_path.search_depth,
                                                 patterns=search_path.patterns,
                                                 include_dirs=search_path.include_dirs,
                                                 exclude_dotdirs=search_path.exclude_dotdirs,
                                                 search_dotdirs=search_path.search_dotdirs)]

        self.items = list(set(items))
        logger.debug(f'Catalog has {len(self.items)} entries')

        # Pre-populate queries for each letter
        for letter in string.ascii_lowercase:
            self.query(letter)
        logger.debug(f'Searches pre-populated')

    def query(self, query_text: str) -> Query:
        if query_text not in self.queries:
            if len(query_text) > 1:
                self.query(query_text[:-1])
                self.queries[query_text] = Query(catalog=self, parent=self.queries[query_text[:-1]], query=query_text)
            else:
                self.queries[query_text] = Query(catalog=self, parent=self, query=query_text)

        return self.queries[query_text]


@dataclass
class Query:
    """Stores a list of Match objects corresponding to a given query string, along with the match scores"""
    query_text: str
    matches: list[Match] = field(repr=False)
    score_results: dict[Path: ScoreResult] = field(repr=False)
    sorted_score_results: tuple[ScoreResult] = field(default=None, repr=False)

    def __init__(self, catalog: Catalog, parent: Catalog | Query, query: str):
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

        self.score_results = {}
        self.sorted_score_results = tuple()
        self.update_query_scores()

    def __repr__(self):
        return f"Query(query_text='{self.query_text}') : {len(self.matches)} matches"

    def update_query_scores(self) -> None:
        self.score_results = {}
        for match in self.matches:
            if match.catalog_item.full_path not in self.score_results or \
                    match.score.result > self.score_results[match.catalog_item.full_path].total_score:
                self.score_results[match.catalog_item.full_path] = ScoreResult(item=match.catalog_item,
                                                                               match=match,
                                                                               total_score=match.score.result)

        self.sorted_score_results = tuple(sorted(self.score_results.values(),
                                                 key=lambda result: result.total_score, reverse=True))

    def update_match_score_if_relevant(self, item_path: Path) -> None:
        if item_path in self.score_results:
            del self.score_results[item_path]
            for match in self.matches:
                if match.catalog_item.full_path == item_path:
                    if item_path in match.catalog.recent_launches:
                        match.score.previously_launched = True
                    else:
                        match.score.previously_launched = False
                    if match.catalog.launch_choices.get(self.query_text, None) == item_path:
                        match.score.is_latest_match = True
                    else:
                        match.score.is_latest_match = False

                    match.score.update_total()

                score_result = self.score_results.get(match.catalog_item.full_path, None)
                if (score_result is None) or (match.score.result > score_result.total_score):
                    self.score_results[match.catalog_item.full_path] = ScoreResult(item=match.catalog_item,
                                                                                   match=match,
                                                                                   total_score=match.score.result)

            self.sorted_score_results = tuple(sorted(self.score_results.values(),
                                                     key=lambda result: result.total_score, reverse=True))

    def print_scores(self, limit: int | None = 10) -> None:
        if limit is None:
            limit = len(self.sorted_score_results)

        total_scores = [result.total_score for result in self.sorted_score_results[:limit]]
        catalog_indices = [result.catalog_index for result in self.sorted_score_results[:limit]]
        full_paths = [result.item.full_path for result in self.sorted_score_results[:limit]]
        item_names = [result.item.full_path.name for result in self.sorted_score_results[:limit]]

        print(f'\n\nQuery: {self.query_text}')
        print(f'{len(self.sorted_score_results)} matches\n')
        print(tabulate({
            'Total Score': total_scores,
            # 'Catalog Index': catalog_indices,
            'Item Name': item_names,
            'Full Path': full_paths,
        }, headers='keys'))

    def print_detailed_scores(self, limit: int | None = 10):
        if limit is None:
            limit = len(self.sorted_score_results)

        total_scores = [result.total_score for result in self.sorted_score_results[:limit]]
        catalog_indices = [result.catalog_index for result in self.sorted_score_results[:limit]]
        item_names = [result.item.full_path.name for result in self.sorted_score_results[:limit]]
        full_paths = [result.item.full_path for result in self.sorted_score_results[:limit]]
        consec_name_scores = [result.match.score.consecutive_name for result in self.sorted_score_results[:limit]]
        initial_letter_scores = [result.match.score.initial_letters_name for result in self.sorted_score_results[:limit]]
        nonconsec_name_scores = [result.match.score.nonconsecutive_name for result in self.sorted_score_results[:limit]]
        last_choice_scores = [result.match.score.is_latest_match for result in self.sorted_score_results[:limit]]
        recent_launch_scores = [result.match.score.previously_launched for result in self.sorted_score_results[:limit]]

        print(f'\n\nQuery: {self.query_text}')
        print(f'{len(self.sorted_score_results)} matches\n')
        print(tabulate({
            'Total Score': total_scores,
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
    """
    Details about a CatalogItem that matches a query string, including:
    - the characters that resulted in the match
    - the indices where those characters were found in the CatalogItem's name
    - the resulting Score object
    """
    catalog_item: CatalogItem
    catalog: Catalog = field(repr=False)
    match_chars: str = field(default_factory=str)
    match_indices: list[int] = field(default_factory=list)
    score: Score | None = None

    def __repr__(self):
        return f"Match: match_chars='{self.match_chars}',match_indices={self.match_indices}, score={self.score}"

    def __post_init__(self):
        new_word_score = 0
        for char_index in self.match_indices:
            if (char_index == 0) or (self.catalog_item.name[char_index - 1] in WORD_SEPARATORS):
                new_word_score += 1

        self.score = Score(catalog_item=self.catalog_item,
                           is_latest_match=self.catalog.launch_choices.get(self.match_chars, None) == self.catalog_item.full_path,
                           previously_launched=self.catalog_item.full_path in self.catalog.recent_launches,
                           nonconsecutive_name=len(self.match_indices),
                           consecutive_name=sum([1 if y-x == 1 else 0 for x, y in
                                                 zip(self.match_indices[:-1], self.match_indices[1:])]),
                           initial_letters_name=new_word_score)


#%%
@dataclass
class Score:
    """Stores the individual components that go into the numerical match score"""
    catalog_item: CatalogItem
    is_latest_match: bool = False
    previously_launched: bool = False
    consecutive_name: float = 0
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
    """Contains the total score for a given Match & CatalogItem"""
    item: CatalogItem
    match: Match = field(repr=False)
    total_score: float
    catalog_index: int | None = None

    def __post_init__(self):
        self.total_score = self.match.score.result
