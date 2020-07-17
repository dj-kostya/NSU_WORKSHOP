import os
import time
import csv
# Type hinting
from typing import List, Tuple


# BASIC SETTINGS
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
        self.timeEndFirst: int = None
        self.timeEndSecond: int = None


    def getTimeEndFirst(self) -> str:
        if not self.timeEndFirst:
            self.timeEndFirst =  self.timeFirst + self.durationFirst
        return self.timeEndFirst

    def getTimeEndSecond(self) -> str:
        if not self.timeEndSecond:
            self.timeEndSecond = self.timeSecond + self.durationSecond
        return self.timeEndSecond


def loadTests(testNum: int, file_path: str = None) -> List[Work]:
    if file_path is None:
        file_path = TEST_PATH + f'inst{testNum}.txt'
    works = []
    with open(file_path, 'r') as f:
        allLines = f.readlines()
        testSize = int(allLines[1])
        lines = allLines[3:]
        for i in range(testSize):
            works.append(Work(i, int(lines[i]), int(lines[i+testSize])))
    return works


def preparingCSV(resultWorks: List[Work], testNum: int, targetValue: int):
    with open(f'gant/GANT-TEST-{testNum}-{targetValue}.csv', 'w', newline='') as csvfile:
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

        self.PICKER_SIZE: int = picker_size
        self.BUFFER_SIZE: int = buffer_size
        self.PACKER_SIZE: int = packer_size
        self.packageStage: List[Work] = []
        self.pickStage: List[Work] = []
        self.bufferStage: List[Work] = []

        self.FREE_PICK_ID: List[int] = []
        self.FREE_PACK_ID: List[int] = []
        self.FREE_BUFFER_ID: List[int] = []
        self.RESULT_WORKS: List[Work] = []

        self.currentTime: int = 0
        self.targetValue: int = 0

        self.hasGoodWorks: bool = False
        self.hasBadWorks: bool = False

        self.goodWorks: List[int] = []
        self.badWorks: List[int] = []

    def getGoodBadWorks(self) -> None:
        if self.hasGoodWorks and self.hasBadWorks:
            return
        for idx in self.idxSequence:
            if self.workList[idx].timeBuffer - self.workList[idx].getTimeEndFirst() > 0:
                self.badWorks.append(idx)
            elif self.workList[idx].timeBuffer == self.workList[idx].getTimeEndFirst() and \
                    self.workList[idx].timeSecond - self.workList[idx].timeBuffer == 0:
                self.goodWorks.append(idx)
        self.hasGoodWorks = True
        self.hasBadWorks = True

    def getGoodWorks(self) -> None:
        if self.hasGoodWorks:
            return
        for idx in self.idxSequence:
            if self.workList[idx].timeBuffer == self.workList[idx].getTimeEndFirst() and \
                    self.workList[idx].timeSecond - self.workList[idx].timeBuffer == 0:
                self.goodWorks.append(idx)
        self.hasGoodWorks = True

    def getBadWorks(self) -> None:
        if self.hasBadWorks:
            return
        for idx in self.idxSequence:
            if self.workList[idx].timeSecond - self.workList[idx].timeBuffer > 0:
                self.badWorks.append(idx)
        self.hasBadWorks = True

    def getLowGrade(self) -> float:
        sum_1 = sum(x.durationFirst for x in self.workList) / self.PICKER_SIZE
        sum_2 = sum(x.durationSecond for x in self.workList) / self.PACKER_SIZE
        min_1 = min(self.workList, key=lambda x: x.durationFirst).durationFirst
        min_2 = min(self.workList,
                    key=lambda x: x.durationSecond).durationSecond
        return max(sum_1 + min_2, sum_2 + min_1)

    def getMinimum(self, array: List[Work], key) -> Work:
        return min(array, key=key)

    def getMinimumPackage(self) -> Work:
        return self.getMinimum(self.packageStage, key=lambda x: x.getTimeEndSecond())

    def getMinimumPicking(self) -> Work:
        return self.getMinimum(self.pickStage, key=lambda x: x.getTimeEndFirst())

    def generateCSV(self, testNum: int) -> None:
        print('Generating CSV file for ', self.targetValue)
        preparingCSV(self.RESULT_WORKS, testNum=testNum,
                     targetValue=self.targetValue)

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
        while self.idxOfIdxSeq < self.seqLen and len(self.pickStage) < self.PICKER_SIZE:
            getNextIndex = self.idxSequence[self.idxOfIdxSeq]
            self.idxOfIdxSeq += 1
            work = self.workList[getNextIndex]
            work.timeFirst = self.currentTime
            work.machineFirstId = self.FREE_PICK_ID.pop()
            self.pickStage.append(work)

    def start(self):
        self.FREE_PICK_ID: List[int] = list(range(self.PICKER_SIZE))
        self.FREE_PACK_ID: List[int] = list(range(self.PACKER_SIZE))
        self.FREE_BUFFER_ID: List[int] = list(range(self.BUFFER_SIZE))
        self.idxOfIdxSeq: int = 0
        self.seqLen = len(self.idxSequence)

        while True:
            if self.pickStage and len(self.bufferStage) < self.BUFFER_SIZE:
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

            while isFirst or (len(self.FREE_BUFFER_ID) < self.BUFFER_SIZE and len(self.FREE_PACK_ID) > 0):
                self.__updatePacking()
                self.__updateBuffer()
                if self.idxOfIdxSeq < self.seqLen or self.pickStage:
                    self.__updatePicking()
                    self.__updateBuffer()
                isFirst = False

            if not self.idxOfIdxSeq < self.seqLen and not self.pickStage and not self.bufferStage and not self.packageStage:
                self.targetValue = minEndTime
                return minEndTime


if __name__ == "__main__":
    TEST_NUM = 0
    testData = loadTests(TEST_NUM)
    seq = [79, 183, 9, 72, 29, 167, 74, 48, 28, 107, 61, 164, 80, 37, 120, 71, 87, 63, 127, 114, 51, 165, 135, 100, 125, 191, 34, 117, 123, 43, 130, 10, 3, 97, 56, 23, 134, 20, 24, 176, 153, 139, 103, 94, 146, 196, 30, 22, 14, 143, 26, 67, 83, 112, 92, 177, 53, 52, 57, 88, 91, 81, 116, 133, 186, 54, 102, 31, 55, 188, 44, 137, 105, 86, 25, 108, 192, 13, 180, 159, 16, 109, 160, 122, 141, 64, 157, 119, 6, 145, 47, 32, 132, 189, 197, 2, 11, 5, 170, 42, 85, 82, 110, 69, 62, 4, 1, 19, 96, 65, 182, 155, 136, 124, 95, 68, 84, 60, 169, 38, 161, 
195, 129, 115, 33, 142, 138, 179, 77, 140, 154, 163, 184, 150, 121, 66, 173, 41, 144, 40, 58, 78, 178, 181, 0, 101, 158, 17, 39, 171, 174, 148, 15, 76, 113, 49, 172, 199, 98, 162, 152, 59, 126, 75, 194, 175, 27, 106, 185, 45, 198, 50, 168, 70, 187, 35, 18, 8, 128, 99, 7, 21, 166, 131, 149, 36, 190, 12, 104, 193, 111, 147, 151, 156, 93, 89, 90, 73, 46, 118]
    decoder = BaseDecoder(testData,seq, 3, 3, 3)
    th_low_grade = decoder.getLowGrade()
    start = time.time()
    result = decoder.start()
    print(f'Времени затрачено:{time.time() - start} с')
    preparingCSV(decoder.RESULT_WORKS, testNum=TEST_NUM,
                 targetValue=decoder.targetValue)
    print('Ответ', decoder.targetValue)
    print('Нижняя оценка', th_low_grade)
    print('Отношение', result/th_low_grade)
    print('Разность', result - th_low_grade)
