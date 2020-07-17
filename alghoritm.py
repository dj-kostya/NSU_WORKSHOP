
from decoder import BaseDecoder, loadTests, Work
from typing import List, Tuple
from crossovers import OX, PMX, smartCross

import random


import time
from tqdm import tqdm


# default settings
TARGER_RESULT = 1.3

NUMBER_ITERATIONS: int = 1500
TEST_NUM: int = 9
PICKER_SIZE: int = 3
PACKER_SIZE: int = 3
BUFFER_SIZE: int = 3


POPULATIONS_SIZE: int = 20
GREED_SIZE: int = 80

LOCAL_SEARCH_ITERATIONS_SIZE: int = 2
LOCAL_SEARCH_POPULATION_SIZE: int = 15
WORK_LIST: List[Work] = loadTests(TEST_NUM)


def getWorstResult(decoders: List[BaseDecoder]) -> BaseDecoder:
    return max(decoders, key=lambda x: x.targetValue)


def getBestResult(decoders: List[BaseDecoder]) -> BaseDecoder:
    return min(decoders, key=lambda x: x.targetValue)


def getWorstResultID(decoders: List[BaseDecoder]) -> int:
    return decoders.index(getWorstResult(decoders))


def getBestResultID(decoders: List[BaseDecoder]) -> int:
    return decoders.index(getBestResult(decoders))


def getNewSequence(firstDecoderIdx: int, secondDecoderIdx: int, decoders: List[BaseDecoder]) -> List[int]:
    # return OX(decoders[firstDecoderIdx].idxSequence, decoders[secondDecoderIdx].idxSequence)
    return smartCross(decoders[firstDecoderIdx], decoders[secondDecoderIdx])


def getNewDecoder(newSequence) -> BaseDecoder:
    decoder = BaseDecoder(WORK_LIST, newSequence, picker_size=PICKER_SIZE,
                          buffer_size=BUFFER_SIZE, packer_size=PACKER_SIZE)
    decoder.start()
    return decoder

def getRandomId():
    return random.randint(0, POPULATIONS_SIZE-1)

def getTwoSequenceID(decoders: List[BaseDecoder]) -> Tuple[int, int]:
    s1, s2 = 0, 0
    while s1 == s2:
        s2 = getBestResultID(decoders)
        s1 = getWorstResultID(decoders)
        if s1 == s2:
            s2 = getRandomId()
    return s1, s2


def useLocalSearch(decoder1) -> BaseDecoder:
    bestDecoder = decoder1
    for _ in range(LOCAL_SEARCH_ITERATIONS_SIZE):
        if bestDecoder.badWorks:
            Idx1 = bestDecoder.badWorks[0]
        else:
            Idx1 = random.randint(0, len(bestDecoder.idxSequence)-1)
        Indexes = list(range(len(bestDecoder.idxSequence)))
        Indexes.pop(Indexes.index(Idx1))
        populationDecoders = []
        for _ in range(LOCAL_SEARCH_POPULATION_SIZE):
            Idx2 = random.choice(Indexes)
            Indexes.pop(Indexes.index(Idx2))
            newSeq = bestDecoder.idxSequence.copy()
            newSeq[Idx1], newSeq[Idx2] = newSeq[Idx2], newSeq[Idx1]
            populationDecoders.append(getNewDecoder(newSeq))
        # newSequences = [sorted(bestDecoder.idxSequence, key=lambda *args: random.random()) for _ in range(LOCAL_SEARCH_POPULATION_SIZE)]

        # populationDecoders = [BaseDecoder(WORK_LIST, newSequence, picker_size=PICKER_SIZE,
        #                                   buffer_size=BUFFER_SIZE, packer_size=PACKER_SIZE) for newSequence in newSequences]

        # populationDecoders = [BaseDecoder(WORK_LIST, newSequence, picker_size=PICKER_SIZE,
        #                                   buffer_size=BUFFER_SIZE, packer_size=PACKER_SIZE) for newSequence in newSequences]
        # for decoder in populationDecoders:
        #     decoder.start()

        newBestDecoder = getBestResult(populationDecoders)
        bestDecoder = min(newBestDecoder, bestDecoder,
                          key=lambda x: x.targetValue)
    return bestDecoder


def genBasePopulation() -> List[BaseDecoder]:
    baseIdxSeq = list(range(len(loadTests(TEST_NUM))))
    populations = [sorted(baseIdxSeq, key=lambda *args: random.random())
                   for i in range(POPULATIONS_SIZE)]
    decoders = []
    # заполняем популяцию
    for population in populations:
        decoders.append(getNewDecoder(population.copy()))
    # генерируем новые решения и изменяем популяцию
    for _ in range(GREED_SIZE - POPULATIONS_SIZE):
        baseIdxSeq = list(range(len(WORK_LIST)))
        item = sorted(baseIdxSeq, key=lambda *args: random.random())
        decoder = getNewDecoder(item)
        max_value_index = getWorstResultID(decoders)
        if(decoder.targetValue < decoders[max_value_index].targetValue):
            decoders[max_value_index] = decoder
            populations[max_value_index] = item

    return decoders


def decodersOut(decoders: List[BaseDecoder], isOnlyStat: bool = False, isOnlyArray: bool = False):
    if not isOnlyStat:
        print('\n'.join([str(decoder.targetValue) for decoder in decoders]))
    if not isOnlyArray:
        bestDecoder = getBestResult(decoders)
        minTargetValue = bestDecoder.targetValue
        thLowGrade = bestDecoder.getLowGrade()
        print(f'Наилушее значение: {minTargetValue}')
        print(f'Нижняя оценка: {thLowGrade}')
        print(f'Отношение: {minTargetValue / thLowGrade}')
        print(f'Разность: {minTargetValue - thLowGrade}')
        print('-'*30)


def GenAlgoritm(isNeedArrayOut: bool = True):
    decoders: List[BaseDecoder] = genBasePopulation()
    if isNeedArrayOut:
        decodersOut(decoders)

    for _ in tqdm(range(NUMBER_ITERATIONS), total=NUMBER_ITERATIONS, desc='Iterations: '):
        s1, s2 = getTwoSequenceID(decoders)
        newSequence = getNewSequence(s1, s2, decoders)
        newDecoder = getNewDecoder(newSequence)

        newDecoder = useLocalSearch(newDecoder)

        worstResultId = getWorstResultID(decoders)

        if newDecoder.targetValue < decoders[worstResultId].targetValue:
            decoders[worstResultId] = newDecoder
    if isNeedArrayOut:
        decodersOut(decoders, isOnlyArray=True)
    bestDecoder = getBestResult(decoders)
    print('Лучший результат до локального поиска: ', bestDecoder.targetValue)
    newDecoder = useLocalSearch(bestDecoder)
    
    decoders.append(newDecoder)
    decodersOut(decoders, isOnlyStat=True)
    return newDecoder

if __name__ == "__main__":
    WORK_LIST: List[Work] = loadTests(TEST_NUM)
    start = time.time()
    bestDecoder = GenAlgoritm()
    print(f'Времени затрачено:{time.time() - start} сек.')
    sep = ','
    filename = bestDecoder.generateCSV(TEST_NUM, sep=sep)
    # from gant import genGant
    # genGant(filename, sep=sep)
