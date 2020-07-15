
from decoder import BaseDecoder, loadTests, Work
from typing import List, Tuple
from random import random

# default settings
TARGER_RESULT = 1.3
TEST_NUM: int = 0
PICKER_SIZE: int = 3
PACKER_SIZE: int = 3
BUFFER_SIZE: int = 3


POPULATIONS: List[List[int]] = []
POPULATIONS_SIZE: int = 10
WORK_LIST: List[Work] = loadTests(TEST_NUM)


def getWorstResultID(populationResult: List[int]) -> int:
    pass


def getBestResultID(populationResult: List[int]) -> int:
    return 1


def getMutationSequence(sequence: List[int]) -> List[int]:
    pass


def getNewSequence(firstSequence: List[int], secondSequence: List[int]) -> List[int]:
    pass


def getTwoSequencesId(populationResult: List[int]) -> Tuple[int, int]:
    return (1, 2)


def genBasePopulation():
    global POPULATIONS
    baseIdxSeq = list(range(len(WORK_LIST)))
    POPULATIONS = [sorted(baseIdxSeq, key=lambda *args: random.random())
                   for i in range(POPULATIONS_SIZE)]


def GenAlgoritm():
    res = None
    testSize = len(WORK_LIST)
    decoders: List[BaseDecoder] = [BaseDecoder(
        population, testSize, picker_size=PICKER_SIZE, packer_size=PACKER_SIZE, buffer_size=BUFFER_SIZE) for population in POPULATIONS
    ]
    populationResult: List[int] = []
    while not res or res < TARGER_RESULT:
        if not populationResult:
            populationResult = [decoder.start() for decoder in decoders]

        firstSequenceId, secondSequenceId = getTwoSequencesId(populationResult)
        firstSequence = decoders[firstSequenceId].idxSequence
        secondSequence = decoders[secondSequenceId].idxSequence

        newSequence = getNewSequence(firstSequence, secondSequence)

        mutationSequence = getMutationSequence(newSequence)
        decoders.append(BaseDecoder(mutationSequence, testSize,
                                    picker_size=PICKER_SIZE, packer_size=PACKER_SIZE, buffer_size=BUFFER_SIZE))
        populationResult.append(decoders[-1].start())
        worstResultId = populationResult()
        populationResult.pop(getWorstResultID(worstResultId))
        decoders.pop(getWorstResultID(worstResultId))
        res = getBestResultID(populationResult)
        bestPopulation = decoders[res]
    pass
