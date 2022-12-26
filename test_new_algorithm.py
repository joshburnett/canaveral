# Some commands meant to be run interactively to explore the performance of
# the cataloging process and ranking algorithm.

from time import perf_counter
from pathlib import Path
import numpy as np
from appdirs import AppDirs

DIRS = AppDirs('Canaveral', appauthor='')

t = perf_counter()
from canaveral.basemodels import Catalog, SearchPathEntry, deep_glob
from loguru import logger

from canaveral.mainwindow import load_search_paths

# %load_ext autoreload
# %autoreload 2


#%%
search_path_entries = [
    SearchPathEntry(path='$user_docs', search_depth=10,
                    patterns=['*.doc', '*.docx', '*.xls', '*.xlsx', '*.ppt',
                              '*.pptx', '*.pdf', '*.txt', '*.vsd', '*.vsdx']),
    SearchPathEntry(path=r'C:\Users\jburnett1\iCloudDrive', search_depth=10,
                    patterns=['.dir', '.doc', '.docx', '.xls', '.xlsx', '.ppt',
                              '.pptx', '.pdf', '.txt', '.vsd', '.vsdx']),
    SearchPathEntry(path='~', search_depth=0, patterns=[''], include_dirs=True),
    SearchPathEntry(path='$user_start_menu', search_depth=3, patterns=['*.lnk']),
    SearchPathEntry(path=r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs',
                    search_depth=3, patterns=['*.lnk']),
]

c = Catalog(search_path_entries, launch_data_file=Path(DIRS.user_data_dir) / 'launch_data.txt')

print(f'{len(c.items)} entries in catalog')

#%%
sorted([item.full_path for item in c.items])

#%%
q = c.query('ff')
q.print_scores(limit=10)

#%%
p = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs'
import os
from fnmatch import fnmatch

dir_entries = list(os.scandir(p))
globs = list(deep_glob(path=Path(p), depth=1, patterns=['*.lnk'], include_dirs=False))

print(f'{len(dir_entries)} entries w/ scandir')
print(f'{len(globs)} entries w/ deep glob')

#%%
pattern = '*.lnk'


#%%
search_path_entries = [
    SearchPathEntry(path='$user_docs', search_depth=10,
                    patterns=['*.doc', '*.docx', '*.xls', '*.xlsx', '*.ppt',
                              '*.pptx', '*.pdf', '*.txt', '*.vsd', '*.vsdx']),
    SearchPathEntry(path=r'C:\Users\jburnett1\iCloudDrive', search_depth=10,
                    patterns=['.dir', '.doc', '.docx', '.xls', '.xlsx', '.ppt',
                              '.pptx', '.pdf', '.txt', '.vsd', '.vsdx']),
    SearchPathEntry(path='~', search_depth=0, patterns=[''], include_dirs=True),
    SearchPathEntry(path='$user_start_menu', search_depth=3, patterns=['*.lnk']),
    SearchPathEntry(path=r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs',
                    search_depth=3, patterns=['*.lnk']),
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
                    patterns=['*.doc', '*.docx', '*.xls', '*.xlsx', '*.ppt',
                              '*.pptx', '*.pdf', '*.txt', '*.vsd', '*.vsdx']),
    SearchPathEntry(path=r'C:\Users\jburnett1\iCloudDrive', search_depth=10,
                    patterns=['*.doc', '*.docx', '*.xls', '*.xlsx', '*.ppt',
                              '*.pptx', '*.pdf', '*.txt', '*.vsd', '*.vsdx']),
    SearchPathEntry(path='~', search_depth=0, patterns=[''], include_dirs=True),
    SearchPathEntry(path='$user_start_menu', search_depth=3, patterns=['*.lnk']),
    SearchPathEntry(path=r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs',
                    search_depth=3, patterns=['*.lnk']),
]

time_descriptions = []
times = [perf_counter()]
queries = []

c = Catalog(search_path_entries)
times.append(perf_counter())
time_descriptions.append(f'Create catalog ({len(c.items)} items)')

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

#%%
q = queries[-2]
# q.print_scores()
q.print_detailed_scores()

q.matches[0]
