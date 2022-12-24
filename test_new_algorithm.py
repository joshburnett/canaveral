# Some commands meant to be run interactively to explore the performance of
# the cataloging process and ranking algorithm.

from time import perf_counter
from pathlib import Path
import numpy as np
from appdirs import AppDirs

DIRS = AppDirs('Canaveral', appauthor='')

t = perf_counter()
from canaveral.basemodels import Catalog, SearchPathEntry
from loguru import logger

from canaveral.mainwindow import load_search_paths

# %load_ext autoreload
# %autoreload 2

#%%
t0 = perf_counter()

#%
# search_path_entries = [
#     SearchPathEntry(path='~', patterns=['[!.]*']),
#     # SearchPathEntry(path='~/code', patterns=['.dir'], search_depth=1),
#     # SearchPathEntry(path='~/Library/Mobile Documents/com~apple~CloudDocs/Code', patterns=['.dir'], search_depth=0),
#     # SearchPathEntry(path='~/Downloads', include_root=True),
# ]

search_path_entries = [
    SearchPathEntry(path='$user_docs', search_depth=10,
                    patterns=['.dir', '.doc', '.docx', '.xls', '.xlsx', '.ppt',
                              '.pptx', '.pdf', '.txt', '.vsd', '.vsdx']),
    # SearchPathEntry(path=r'C:\Users\jburnett1\iCloudDrive', search_depth=10,
    #                 patterns=['.dir', '.doc', '.docx', '.xls', '.xlsx', '.ppt',
    #                           '.pptx', '.pdf', '.txt', '.vsd', '.vsdx']),
    SearchPathEntry(path='~', search_depth=0, patterns=['.dir']),
    SearchPathEntry(path='$user_start_menu', search_depth=3, patterns=['.lnk']),
    SearchPathEntry(path=r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs', search_depth=3, patterns=['.lnk']),
]

# search_path_entries = load_search_paths(Path(DIRS.user_data_dir) / 'paths.toml')

t1 = perf_counter()

c = Catalog(search_path_entries, launch_data_file=Path('canaveral/launch_data.txt'))
print(f'Catalog has {len(c.items)} entries')
# c.items

t2 = perf_counter()

print(f'Imports: {t0-t:.2f} sec')
print(f'Loading search entries: {t1-t0:.2f} sec')
print(f'Catalog scanning: {t2-t1:.2f} sec')


#%%
search_path_entries = [
    SearchPathEntry(path='$user_docs', search_depth=10,
                    patterns=['.dir', '.doc', '.docx', '.xls', '.xlsx', '.ppt',
                              '.pptx', '.pdf', '.txt', '.vsd', '.vsdx']),
    # SearchPathEntry(path=r'C:\Users\jburnett1\iCloudDrive', search_depth=10,
    #                 patterns=['.dir', '.doc', '.docx', '.xls', '.xlsx', '.ppt',
    #                           '.pptx', '.pdf', '.txt', '.vsd', '.vsdx']),
    SearchPathEntry(path='~', search_depth=0, patterns=['.dir']),
    SearchPathEntry(path='$user_start_menu', search_depth=3, patterns=['.lnk']),
    SearchPathEntry(path=r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs', search_depth=3, patterns=['.lnk']),
]

times = [perf_counter()]
c = Catalog(search_path_entries)
times.append(perf_counter())

logger.debug(f'Catalog has {len(c.items)} entries')

queries = []

q_text = 'python'
for n in range(len(q_text)):
    queries.append(c.query(q_text[:n+1]))
    times.append(perf_counter())

etimes = [y-x for x, y in zip(times[:-1], times[1:])]

print(etimes)

for q in queries:
    q.print_scores()


#%%
search_path_entries = [
    SearchPathEntry(path='$user_docs', search_depth=10,
                    patterns=['.dir', '.doc', '.docx', '.xls', '.xlsx', '.ppt',
                              '.pptx', '.pdf', '.txt', '.vsd', '.vsdx']),
    # SearchPathEntry(path=r'C:\Users\jburnett1\iCloudDrive', search_depth=10,
    #                 patterns=['.dir', '.doc', '.docx', '.xls', '.xlsx', '.ppt',
    #                           '.pptx', '.pdf', '.txt', '.vsd', '.vsdx']),
    SearchPathEntry(path='~', search_depth=0, patterns=['.dir']),
    SearchPathEntry(path='$user_start_menu', search_depth=3, patterns=['.lnk']),
    SearchPathEntry(path=r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs', search_depth=3, patterns=['.lnk']),
]

time_descriptions = []
times = [perf_counter()]
queries = []

c = Catalog(search_path_entries)
times.append(perf_counter())
time_descriptions.append('Create catalog')

queries.append(c.query('s'))
times.append(perf_counter())
time_descriptions.append("Query 's'")

queries.append(c.query('sh'))
times.append(perf_counter())
time_descriptions.append("Query 'sh'")

queries.append(c.query('sho'))
times.append(perf_counter())
time_descriptions.append("Query 'sho'")

queries.append(c.query('shop'))
times.append(perf_counter())
time_descriptions.append("Query 'shop'")

queries.append(c.query('shot'))
times.append(perf_counter())
time_descriptions.append("Query 'shot'")

queries.append(c.query('shoot'))
times.append(perf_counter())
time_descriptions.append("Query 'shoot'")

time_deltas = np.diff(np.array(times))
total_time = times[-1] - times[0]

print('\n\n')

for delta, description in zip(time_deltas, time_descriptions):
    print(f'Delta: {delta*1000:0.2f} ms\tItem: {description}')

q = queries[-2]
# q.print_scores()
q.print_detailed_scores()

q.matches[0]

#%%
from pathlib import Path
from canaveral.basemodels import deep_glob
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
