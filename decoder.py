import os
import time

# Type hinting
from typing import List

#Logging 
import logging
from datetime import datetime
logging.basicConfig(level=logging.DEBUG, filename=f'logs/logs-{datetime.now().strftime("%d-%m-%Y-%H-%M-%S")}.logs', format='%(message)s')
logging.info('len(firstStage);len(buffer);len(secondStage);currentTime')

TEST_SIZE: int = 2000
TEST_NUM: int = 10
TEST_PATH: str = 'tests/'
TEST_DATA: list = []


FIRST_STAGE_SIZE: int = 3
SECOND_STAGE_SIZE: int = 3
BUFFER_SIZE: int = 3


currentTime: int = 0
firstStage = []
secondStage = []  # время освобождение
buffer = []


class Work:
    def __init__(self, id: int, durationFirst: int, durationSecond: int):
        self.id: int = id
        self.durationFirst: int = durationFirst
        self.durationSecond: int = durationSecond
        self.timeFirst: int = None

    def getTimeEndFirst(self) -> str:
        return self.timeFirst + self.durationFirst


def loadTests(file_path: str = None) -> List[Work]:
    if file_path is None:
        file_path = TEST_PATH + f'inst{TEST_NUM}.txt'
    works = []
    with open(file_path, 'r') as f:
        lines = f.readlines()[3:]
        for i in range(TEST_SIZE):
            works.append(Work(i, int(lines[i]), int(lines[i+TEST_SIZE])))
    return works


def updateSecond():
    """
        Function pop all ready tasks from second line
    """
    global secondStage
    if not secondStage:
        return
    minSecond = min(secondStage)
    while currentTime >= minSecond:
        minSecondIdx = secondStage.index(minSecond)
        secondStage.pop(minSecondIdx)
        if not secondStage:
            return
        minSecond = min(secondStage)


def updateBuffer():
    """
        Function pop from buffer to second line
    """
    global buffer, secondStage
    if not buffer:
        return
    while len(secondStage) < SECOND_STAGE_SIZE and buffer:
        work = buffer.pop(0)
        secondStage.append(currentTime + work.durationSecond)


def updateFirst():
    """
        Function pop all ready tasks from first line to buffer. And if first line has free space then push work from TEST_DATA
    """
    global firstStage, buffer, secondStage, currentTime
    if firstStage:
        minFirst = min(firstStage, key=lambda x: x.getTimeEndFirst())
    while firstStage and currentTime >= minFirst.getTimeEndFirst() and len(buffer) < BUFFER_SIZE:
        minFirstIdx = firstStage.index(minFirst)
        buffer.append(firstStage.pop(minFirstIdx))
        if not firstStage:
            break
        minFirst = min(firstStage, key=lambda x: x.getTimeEndFirst())
    while TEST_DATA and len(firstStage) < FIRST_STAGE_SIZE:
        work = TEST_DATA.pop(0)
        work.timeFirst = currentTime
        firstStage.append(work)


def low_grade() -> float:
    global firstStage, buffer, secondStage, currentTime
    sum_1 = sum([i.durationFirst for i in TEST_DATA])/FIRST_STAGE_SIZE
    sum_2 = sum([i.durationSecond for i in TEST_DATA])/SECOND_STAGE_SIZE
    min_1 = min(TEST_DATA, key=lambda x: x.durationSecond).durationFirst
    min_2 = min(TEST_DATA, key=lambda x: x.durationSecond).durationSecond
    return min(sum_1 + min_2, sum_2 + min_1)


def main():
    global firstStage, buffer, secondStage, currentTime
    while True:
        logging.debug(f'{len(firstStage)};{len(buffer)};{len(secondStage)};{currentTime}')
       
        if firstStage and len(buffer) < BUFFER_SIZE:
            minEndFirst = min(
                firstStage, default=0, key=lambda x: x.getTimeEndFirst()).getTimeEndFirst()
        else:
            minEndFirst = None
        minEndTime = minEndFirst
        if secondStage:
            minEndSecond = min(secondStage)
            if minEndTime:
                minEndTime = min(minEndSecond, minEndTime)
            else:
                minEndTime = minEndSecond

        currentTime = 0 if not minEndTime else minEndTime
        updateSecond()
        updateBuffer()
        if TEST_DATA or firstStage:
            updateFirst()
            updateBuffer()

        if not TEST_DATA and not firstStage and not secondStage:
            return minEndTime


if __name__ == "__main__":
    TEST_DATA = loadTests()
    th_low_grade = low_grade()
    start = time.time()
    result = main()
    print(f'Времени затрачено:{time.time() - start} с')
    print('Ответ', result)
    print('Нижняя оценка', th_low_grade)
    print('Отношение', result/th_low_grade)
    print('Разность', result - th_low_grade)
