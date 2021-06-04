from __future__ import annotations

from pathlib import Path
from basemodels import SearchPathEntry, Catalog, QuerySet, CatalogItem
from time import perf_counter

from dataclasses import dataclass, replace
from typing import List, Union, Optional, Dict


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
time_descriptions = []
times = [perf_counter()]

c = Catalog(search_path_entries)

#%%
"""
Node fields:

- Catalog reference
- Search text so far
- List of matching char indices
- List of matching catalog items
- Dict of subqueries: keys are subquery text (query_so_far + one char), values are lists of resulting nodes (one node
    for each valid location of the new character)

Methods:
- Create sub-query
- Query (returns list of matching catalog items and their scores)
    - Recursively drills down one character at a time until there is no appropriate sub-query.
      Creates sub-queries as needed. When it reaches the final query, it calculates the scores for each of
      the remaining matches and returns a dictionary with items as keys and scores as the values.

"""


#%%
@dataclass
class SearchNode:
    catalog: Catalog
    query_so_far: str
    match_char_indices: List[int]
    matches: List[CatalogItem]
    children: Dict[str:SearchNode]
    """
    This won't actually work. Need to make a dict of the matches, with child query nodes under each match.
    """
