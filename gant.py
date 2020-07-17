import pandas as pd
from copy import copy
import numpy as np

TEST_NUM = 0
FIRST_STAGE_SIZE: int = 3
SECOND_STAGE_SIZE: int = 3
BUFFER_SIZE: int = 3
FILENAME = "GANT-TEST-0-1117"

data = pd.read_csv(f'gant/{FILENAME}.csv', sep=',')#здесь ваш файл с расширением .csv
data.set_index(['work_id'], inplace=True)
data.sort_values(by=['start_pick'], inplace=True)


import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from itertools import cycle

color = {'blank': 'w',
         'block': 'tab:gray',
         'pick': cycle(['tab:orange', 'tab:red']),
         'buff': cycle(['tab:olive', 'tab:cyan']),
         'pack': cycle(['tab:purple', 'tab:pink'])}

fig, ax = plt.subplots(figsize=(200,10))#эти параметры определяют ширину и высоту прямоугольников в итоговом расписании
yaxis = 1                               #рекомендую для размерности работ 200 использовать параметры (400,16)
height = 0.9
yticks = []
xticks = [0]
yticklabels = []

for work_type in ['pick_id', 'buff_id', 'pack_id']:
    work_type = work_type.split('_')[0]
    work_group = data[['start_' + work_type, 'finish_' + work_type, 'real_time']].groupby([data[work_type + '_id']])
    for worker in work_group.groups.keys():
        works = []
        colors = []
        worker_routine = work_group.get_group(worker)
        for work_id in worker_routine.index:
            dur = worker_routine.at[work_id, 'finish_' + work_type] - worker_routine.at[work_id, 'start_' + work_type]
            if not dur:
                continue
            if work_type == 'pick':
                block_start = worker_routine.at[work_id, 'start_' + work_type] + worker_routine.at[work_id, 'real_time']
                block_dur = worker_routine.at[work_id, 'finish_' + work_type] - block_start
                if not block_dur:
                    works.append((worker_routine.at[work_id, 'start_' + work_type], dur))
                    center =  worker_routine.at[work_id, 'start_' + work_type] + (dur) / 2
                    colors.append(next(color.get(work_type)))
                    ax.text(center, yaxis + height / 2, f'{work_id}', ha="center", va="center", color="black",  rotation=90, fontsize=8)
                    xticks.append(worker_routine.at[work_id, 'finish_' + work_type])
                else:
                    works.append((worker_routine.at[work_id, 'start_' + work_type], worker_routine.at[work_id, 'real_time']))
                    center =  worker_routine.at[work_id, 'start_' + work_type] + (worker_routine.at[work_id, 'real_time']) / 2
                    colors.append(next(color.get(work_type)))
                    ax.text(center, yaxis + height / 2, f'{work_id}', ha="center", va="center", color="black",  rotation=90, fontsize=8)
                    xticks.append(worker_routine.at[work_id, 'start_' + work_type] + worker_routine.at[work_id, 'real_time'])
                    
                    block = (block_start, block_dur)
                    works.append((block_start, block_dur))
                    center =  block_start + (block_dur) / 2
                    colors.append(color.get('block'))
                    ax.text(center, yaxis + height / 2, f'b', ha="center", va="center", color="black",  rotation=90, fontsize=8)#(*)fontsize - размер шрифта надписи на работе. менять синхронно с (**)
                    xticks.append(block_start + block_dur)
            else:
                works.append((worker_routine.at[work_id, 'start_' + work_type], dur))
                center =  worker_routine.at[work_id, 'start_' + work_type] + (dur) / 2
                colors.append(next(color.get(work_type)))
                ax.text(center, yaxis + height / 2, f'{work_id}', ha="center", va="center", color="black",  rotation=90, fontsize=8)#(**)fontsize - размер шрифта надписи на работе. менять синхронно с (*)
                xticks.append(worker_routine.at[work_id, 'finish_' + work_type])
        works = np.array(works, dtype=[('start', int), ('dur', int)])
        works = np.sort(works, order='start')
        ax.broken_barh(works, (yaxis, height), facecolors=colors, alpha=0.75, edgecolor='black', linewidth=0.5)#linewidth - толщина границ прямоугольников
        yticks.append(yaxis + height / 2)
        yaxis += 1
        yticklabels.append(f'{worker}')
ax.set_ylim(0.5, yaxis + 0.5)
ax.set_xlim(-1, int(ax.get_xlim()[1]) - 10)
ax.set_xlabel('units since start')
ax.set_yticks(yticks)
ax.set_xticks(xticks)
ax.set_yticklabels(yticklabels, {'fontsize': 20})#размер щрифта подписей оси Y
ax.set_xticklabels(xticks, {'fontsize': 7})#размер щрифта подписей оси X
ax.set_axisbelow(True)
ax.autoscale(enable=True, axis='x', tight=True)
ax.grid(True)
fig.savefig(f'gant/{FILENAME}.svg', format='svg')#с таким названием будет сохранен итог в формате .svg