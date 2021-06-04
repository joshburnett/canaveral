from pathlib import Path
from basemodels import SearchPathEntry, Catalog, QuerySet
from time import perf_counter
import numpy as np

from memorysize import get_size


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
times.append(perf_counter())
time_descriptions.append('Create catalog')

qs = QuerySet(catalog=c)
times.append(perf_counter())
time_descriptions.append('Create empty QuerySet')

qs.create_query('s')
times.append(perf_counter())
time_descriptions.append("Query 's'")

qs.create_query('sh')
times.append(perf_counter())
time_descriptions.append("Query 'sh'")

qs.create_query('sho')
times.append(perf_counter())
time_descriptions.append("Query 'sho'")

qs.create_query('shop')
times.append(perf_counter())
time_descriptions.append("Query 'shop'")

qs.create_query('shot')
times.append(perf_counter())
time_descriptions.append("Query 'shot'")

qs.create_query('shoot')
times.append(perf_counter())
time_descriptions.append("Query 'shoot'")

time_deltas = np.diff(np.array(times))
total_time = times[-1] - times[0]

print('\n\n')

for delta, description in zip(time_deltas, time_descriptions):
    print(f'Delta: {delta*1000:0.2f} ms\tItem: {description}')


#%%
c = Catalog(search_path_entries)
qs = QuerySet(catalog=c)

qs.create_query('test')
