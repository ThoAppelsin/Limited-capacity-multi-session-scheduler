import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path
from pprint import pprint
from itertools import combinations
from alive_progress import alive_bar
from math import comb

### import data

files = Path('./data').glob('*.xlsx')
dfs = []

for f in files:
	df = pd.read_excel(f, index_col=None, header=0)
	df['file'] = f.stem
	dfs.append(df)

df = pd.concat(dfs, ignore_index=True)

qstring = 'Q01_doluluklar->'
df.columns = [x.split()[0][len(qstring):] if x.startswith(qstring) else x for x in df.columns]

### define triplets

triplets = {day + ''.join(str(i) for i in range(b, b+3)) : list(day + str(i) for i in range(b, b+3))
	for day in ['W', 'Th', 'F'] # 'M', 'T'
	for b in range(1, 5 if day == 'T' else 7)}

### extract available triplets

for tripletstr, tripletslots in triplets.items():
	df[tripletstr] = (df[tripletslots] == 0).all(axis=1)

# ### define slots

# triplets = [tuple(day + str(i) for i in range(b, b+3))
# 	for day in ['M', 'T', 'W', 'Th', 'F']
# 	for b in range(1, 5 if day == 'T' else 7)]

# triplet_suitors = {triplet: [] for triplet in triplets}

# ### extract available slots

# def available_triplets(row):
# 	for triplet, suitors in triplet_suitors.items():
# 		if all(row[slot] == 0 for slot in triplet):
# 			suitors.append(row['Full name'])
# 			yield triplet

# df['available_triplets'] = df.apply(lambda x: list(available_triplets(x)), axis=1)

### find the best set

# labsets = {labset: len(df[df[iter(labset)].any(axis=1)]) for labset in combinations(triplets, 5)}
totalstu = 389
capacity = 88 * len(df) // totalstu
print("assumed capacity:", capacity)
labsets = dict()
with alive_bar(comb(len(triplets), 5)) as bar:
	for labset in combinations(triplets, 5):
		vacant_trips = list(labset)
		dfv = df.loc[:, vacant_trips]
		labsetassignments = {triplet: [] for triplet in vacant_trips}
		labsetassignments['out'] = []

		def sort():
			global dfv
			dfv = dfv.sort_values('avails')

		def init():
			global dfv, vacant_trips
			dfv.loc[:, 'avails'] = dfv.loc[:, vacant_trips].sum(axis=1)
			sort()

		def droptriplet():
			global triplet, vacant_trips
			vacant_trips.remove(triplet)
			init()

		def listavails(i):
			global vacant_trips, dfv
			return np.array(vacant_trips)[dfv.iloc[i, (dfv.columns.get_loc(t) for t in vacant_trips)].values.astype(bool)]

		init()
		
		while len(dfv) > 0:

			### assign all unavailables
			if dfv.iloc[0, dfv.columns.get_loc('avails')] == 0:
				labsetassignments['out'] += dfv.loc[dfv.loc[:, 'avails'] == 0, :].index.tolist()
				dfv = dfv.loc[dfv.loc[:, 'avails'] > 0, :]

			### assign some availables
			else:
				### assign all desperates
				if dfv.iloc[0, dfv.columns.get_loc('avails')] == 1:
					triplet = listavails(0)[0]

					assignees = dfv.loc[:, 'avails'] == 1 & dfv.loc[:, triplet]
					assignee_indices = assignees.index[assignees]
			
				### assign one of the rest
				else:
					triplets = listavails(0)
					### choose the triplet with the least nr of assignments
					triplet = min(triplets, key=lambda t: len(labsetassignments[t]))
					assignee_indices = dfv.index[0:1]


				dfv = dfv.drop(assignee_indices)

				### allocate vacancies
				tripletassignments = labsetassignments[triplet]
				vacancy = capacity - len(tripletassignments)
				tripletassignments += assignee_indices[:vacancy].tolist()
				if len(assignee_indices) >= vacancy:
					### this triplet is not an option anymore
					droptriplet()
					### trash the rest (if any); THIS WILL BE DONE ON THE NEXT ITER
					# labsetassignments['out'] += assignee_indices[vacancy:]

		labsets[labset] = labsetassignments
		# labsetassignments = sum(dfv['avails'] > 0)

		bar()

pprint(sorted(((len(v['out']), k) for k, v in labsets.items()), reverse=True))

# pprint({k: len(v) for k, v in triplet_suitors.items()})

# print(len(df.loc[df[iter(('F567', 'F678'))].all(axis=1)]))


# print(list(combinations(triplets, 5)))