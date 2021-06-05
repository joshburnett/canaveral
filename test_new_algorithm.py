from basemodels import Catalog, SearchPathEntry
from time import perf_counter
from loguru import logger

from paths import search_path_entries

#%
# search_path_entries = [
#     SearchPathEntry(path='~', patterns=['[!.]*']),
#     # SearchPathEntry(path='~/code', patterns=['.dir'], search_depth=1),
#     # SearchPathEntry(path='~/Library/Mobile Documents/com~apple~CloudDocs/Code', patterns=['.dir'], search_depth=0),
#     # SearchPathEntry(path='~/Downloads', include_root=True),
# ]
#
# c = Catalog(search_path_entries)
# print(f'Catalog has {len(c.items)} entries')
# c.items


#%%
times = [perf_counter()]
c = Catalog(search_path_entries)
times.append(perf_counter())

logger.debug(f'Catalog has {len(c.items)} entries')

q = c.query('l')
times.append(perf_counter())
q = c.query('lo')
times.append(perf_counter())
q = c.query('lov')
times.append(perf_counter())
q = c.query('love')
times.append(perf_counter())

etimes = [y-x for x, y in zip(times[:-1], times[1:])]


#%%
from pathlib import Path
from basemodels import deep_glob
from pprint import pp
p = Path('/Users/josh')

# a = list(deep_glob(p, pattern='[!.]*'))
a = list(deep_glob(p, pattern='[!.]*', include_dotdirs=True))
# a = list(deep_glob(p, pattern='*'))
pp(a)
print(f'List has {len(a)} entries')
