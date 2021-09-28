# Some commands meant to be run interactively to explore the performance of
# the cataloging process and ranking algorithm.

from time import perf_counter
from pathlib import Path
import numpy as np

t0 = perf_counter()
from basemodels import Catalog
from loguru import logger

from paths import search_path_entries

#%
# search_path_entries = [
#     SearchPathEntry(path='~', patterns=['[!.]*']),
#     # SearchPathEntry(path='~/code', patterns=['.dir'], search_depth=1),
#     # SearchPathEntry(path='~/Library/Mobile Documents/com~apple~CloudDocs/Code', patterns=['.dir'], search_depth=0),
#     # SearchPathEntry(path='~/Downloads', include_root=True),
# ]

t1 = perf_counter()

c = Catalog(search_path_entries, launch_data_file=Path('canaveral/launch_data.txt'))
print(f'Catalog has {len(c.items)} entries')
# c.items

t2 = perf_counter()

print(f'Imports: {t1-t0:.2f} sec')
print(f'Catalog scanning: {t2-t1:.2f} sec')


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
time_descriptions = []
times = [perf_counter()]

c = Catalog(search_path_entries)
times.append(perf_counter())
time_descriptions.append('Create catalog')

q = c.query('s')
times.append(perf_counter())
time_descriptions.append("Query 's'")

q = c.query('sh')
times.append(perf_counter())
time_descriptions.append("Query 'sh'")

q = c.query('sho')
times.append(perf_counter())
time_descriptions.append("Query 'sho'")

q = c.query('shop')
times.append(perf_counter())
time_descriptions.append("Query 'shop'")

q = c.query('shot')
times.append(perf_counter())
time_descriptions.append("Query 'shot'")

q = c.query('shoot')
times.append(perf_counter())
time_descriptions.append("Query 'shoot'")

time_deltas = np.diff(np.array(times))
total_time = times[-1] - times[0]

print('\n\n')

for delta, description in zip(time_deltas, time_descriptions):
    print(f'Delta: {delta*1000:0.2f} ms\tItem: {description}')

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



#%%
q = c.query('ff')
q.print_scores()
