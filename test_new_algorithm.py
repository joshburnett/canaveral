from __future__ import annotations

from pathlib import Path
from basemodels import SearchPathEntry, Catalog, QuerySet, CatalogItem, Query, Match, findall
from time import perf_counter

from dataclasses import dataclass, replace, field
from typing import List, Union, Optional, Dict
from memorysize import get_size

import platform

#%%
system = platform.system()
if system == 'Windows':
    search_path_entries = [
        SearchPathEntry(path=Path(r'C:\Users\jburnett1\OneDrive - Werfen\Documents\! Beacon')),
        SearchPathEntry(path=Path(r'C:\Users\jburnett1\code'), patterns=['.dir']),
        SearchPathEntry(
            path=Path(r'C:\Users\jburnett1\AppData\Roaming\Microsoft\Windows\Start Menu\Programs'), patterns=['*.lnk']
        ),
        SearchPathEntry(path=Path(r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs'), patterns=['*.lnk'])
    ]
elif system == 'Darwin':
    search_path_entries = [
        SearchPathEntry(path=Path('~')),
        SearchPathEntry(path=Path('~/code'), patterns=['.dir']),
        SearchPathEntry(path=Path('~/Downloads')),
        SearchPathEntry(path=Path('/Users/josh/Library/Mobile Documents/com~apple~CloudDocs'))
    ]
else:
    raise RuntimeError('Platform must be Windows or Darwin')

#%%
times = [perf_counter()]
c = Catalog(search_path_entries)
times.append(perf_counter())

q = c.query('l')
times.append(perf_counter())
q = c.query('lo')
times.append(perf_counter())
q = c.query('lov')
times.append(perf_counter())
q = c.query('love')
times.append(perf_counter())

etimes = [y-x for x, y in zip(times[:-1], times[1:])]
