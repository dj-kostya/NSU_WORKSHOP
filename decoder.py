import os
import time
import csv
# Type hinting
from typing import List, Tuple

# Logging
import logging
from datetime import datetime
logging.basicConfig(level=logging.DEBUG,
                    filename=f'logs/logs-{datetime.now().strftime("%d-%m-%Y-%H-%M-%S")}.logs', format='%(message)s')
logging.info('len(firstStage);len(buffer);len(secondStage);currentTime')

# BASIC SETTINGS
TEST_SIZE: int = 200
TEST_NUM: int = 0
FIRST_STAGE_SIZE: int = 3
BUFFER_SIZE: int = 3
SECOND_STAGE_SIZE: int = 3
TEST_PATH: str = 'tests/'


class Work:
    def __init__(self, id: int, durationFirst: int, durationSecond: int):
        self.id: int = id
        self.durationFirst: int = durationFirst
        self.durationSecond: int = durationSecond
        self.timeFirst: int = None
        self.timeSecond: int = None
        self.timeBuffer: int = None
        self.machineFirstId: int = None
        self.machineSecondId: int = None
        self.machineBufferId: int = None

    def getTimeEndFirst(self) -> str:
        return self.timeFirst + self.durationFirst

    def getTimeEndSecond(self) -> str:
        return self.timeSecond + self.durationSecond

    def getFirstTiming(self) -> Tuple[int, int]:
        return (self.timeFirst, self.getTimeEndFirst())

    def getSecondTiming(self) -> Tuple[int, int]:
        return (self.timeSecond, self.getTimeEndSecond())

    def getBufferTiming(self) -> Tuple[int, int]:
        return (self.timeBuffer, self.timeSecond)


def loadTests(testNum: int, file_path: str = None) -> List[Work]:
    if file_path is None:
        file_path = TEST_PATH + f'inst{testNum}.txt'
    works = []
    with open(file_path, 'r') as f:
        lines = f.readlines()[3:]
        for i in range(TEST_SIZE):
            works.append(Work(i, int(lines[i]), int(lines[i+TEST_SIZE])))
    return works


def preparingCSV(resultWorks: List[Work]):
    with open(f'gant/GANT-TEST-{TEST_NUM}-{FIRST_STAGE_SIZE}-{BUFFER_SIZE}-{SECOND_STAGE_SIZE}.csv', 'w', newline='') as csvfile:
        fieldnames = ['work_id', 'start_pick', 'finish_pick', 'start_buff', 'finish_buff', 'start_pack', 'finish_pack', 'pick_id', 'buff_id', 'pack_id',
                      'real_time']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for work in resultWorks:
            writer.writerow({
                'work_id': work.id,
                'start_pick': work.timeFirst,
                'finish_pick': work.getTimeEndFirst(),
                'start_buff': work.timeBuffer,
                'finish_buff': work.timeSecond,
                'start_pack': work.timeSecond,
                'finish_pack': work.getTimeEndSecond(),
                'pick_id': work.machineFirstId,
                'buff_id': work.machineBufferId,
                'pack_id': work.machineSecondId,
                'real_time': work.durationFirst
            })


class BaseDecoder:

    def __init__(self, workList: List[Work], idxSequence: List[int], picker_size: int, buffer_size: int, packer_size: int):
        self.workList: List[Work] = workList
        self.idxSequence: List[int] = idxSequence
        self.idxSequenceCopy: List[int] = idxSequence.copy()
        self.PICKER_SIZE: int = picker_size
        self.BUFFER_SIZE: int = buffer_size
        self.PACKER_SIZE: int = packer_size
        self.packageStage: List[Work] = []
        self.pickStage: List[Work] = []
        self.bufferStage: List[Work] = []

        self.FREE_PICK_ID: List[int] = list(range(self.PICKER_SIZE))
        self.FREE_PACK_ID: List[int] = list(range(self.PACKER_SIZE))
        self.FREE_BUFFER_ID: List[int] = list(range(self.BUFFER_SIZE))
        self.RESULT_WORKS: List[Work] = []

        self.currentTime = 0

    def getLowGrade(self) -> float:
        sum_1 = sum(self.workList, key=lambda x: x.durationFirst) / \
            self.PICKER_SIZE
        sum_2 = sum(self.workList, key=lambda x: x.durationSecond) / \
            self.PACKER_SIZE
        min_1 = min(self.workList, key=lambda x: x.durationFirst).durationFirst
        min_2 = min(self.workList,
                    key=lambda x: x.durationSecond).durationSecond
        return min(sum_1 + min_2, sum_2 + min_1)

    def getMinimum(self, array: List[Work], key) -> Work:
        return min(array, key=key)

    def getMinimumPackage(self) -> Work:
        return self.getMinimum(self.packageStage, key=lambda x: x.getTimeEndSecond())

    def getMinimumPicking(self) -> Work:
        return self.getMinimum(self.pickStage, key=lambda x: x.getTimeEndFirst())

    def __updatePacking(self):
        """
            Function pop all ready tasks from second line
        """
        if not self.packageStage:
            return
        minSecond = self.getMinimumPackage()
        while self.currentTime >= minSecond.getTimeEndSecond():
            minSecondIdx = self.packageStage.index(minSecond)
            work = self.packageStage.pop(minSecondIdx)
            self.FREE_PACK_ID.append(work.machineSecondId)
            self.RESULT_WORKS.append(work)
            if not self.packageStage:
                return
            minSecond = self.getMinimumPackage()

    def getIdxToPopFromBuffer(self, stage: int):
        """
            Function which choices which work will be pop from stage.
        """
        return 0

    def __updateBuffer(self):
        """
            Function pop from buffer to second line
        """
        if not self.bufferStage:
            return
        while len(self.packageStage) < self.PACKER_SIZE and self.bufferStage:
            work = self.bufferStage.pop(self.getIdxToPopFromBuffer(stage=1))
            work.timeSecond = self.currentTime
            work.machineSecondId = self.FREE_PACK_ID.pop()
            self.FREE_BUFFER_ID.append(work.machineBufferId)
            self.packageStage.append(work)

    def __updatePicking(self):
        if self.pickStage:
            minFirst = self.getMinimumPicking()
        while self.pickStage and self.currentTime >= minFirst.getTimeEndFirst() and len(self.bufferStage) < self.BUFFER_SIZE:
            minFirstIdx = self.pickStage.index(minFirst)
            work = self.pickStage.pop(minFirstIdx)
            work.timeBuffer = self.currentTime
            work.machineBufferId = self.FREE_BUFFER_ID.pop()
            self.bufferStage.append(work)
            self.FREE_PICK_ID.append(work.machineFirstId)
            if not self.pickStage:
                break
            minFirst = self.getMinimumPicking()
        while self.idxSequenceCopy and len(self.pickStage) < FIRST_STAGE_SIZE:
            getNextIndex = self.idxSequenceCopy.pop()
            work = self.workList[getNextIndex]
            work.timeFirst = self.currentTime
            work.machineFirstId = self.FREE_PICK_ID.pop()
            self.pickStage.append(work)

    def start(self):
        while True:
            if self.pickStage and len(self.bufferStage) < BUFFER_SIZE:
                minEndTime = self.getMinimumPicking().getTimeEndFirst()
            else:
                minEndTime = None

            if self.packageStage:
                minEndPacking = self.getMinimumPackage().getTimeEndSecond()
                if minEndTime:
                    minEndTime = min(minEndTime, minEndPacking)
                else:
                    minEndTime = minEndPacking

            self.currentTime = minEndTime if minEndTime else 0
            isFirst = True
            while isFirst or (len(self.FREE_BUFFER_ID) < BUFFER_SIZE and len(self.FREE_PACK_ID) > 0):
                self.__updatePacking()
                self.__updateBuffer()
                if self.idxSequenceCopy or self.pickStage:
                    self.__updatePicking()
                    self.__updateBuffer()
                isFirst = False

            if not self.idxSequenceCopy and not self.pickStage and not self.bufferStage and not self.packageStage:
                return minEndTime


if __name__ == "__main__":

    testData = loadTests(TEST_NUM)
    decoder = BaseDecoder(testData, list(range(len(testData))), 3, 3, 3)
    th_low_grade = decoder.getLowGrade()
    start = time.time()
    result = decoder.start()
    print(f'Времени затрачено:{time.time() - start} с')
    preparingCSV(decoder.RESULT_WORKS)
    print('Ответ', result)
    print('Нижняя оценка', th_low_grade)
    print('Отношение', result/th_low_grade)
    print('Разность', result - th_low_grade)
