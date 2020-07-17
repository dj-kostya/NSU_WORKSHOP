import random
from decoder import BaseDecoder, Work
from typing import List, Tuple

def testSequence(seq1):
    for i in range(len(seq1)):
        for j in range(len(seq1)):
            if i != j and seq1[i] == seq1[j]:
                print('crossover failed')

def PMX(parent1, parent2):
    p1 = parent1.copy()
    p2 = parent2.copy()

    n = len(p1)
    c1 = [-1] * n
    c2 = [-1] * n
    cut1 = random.randint(0, n-1)
    step = random.randint(40, 50)
    cut2 = (cut1 + step) % 200
    cut1, cut2 = sorted([cut1, cut2])
    c1[cut1:cut2] = p1[cut1:cut2]
    c2[cut1:cut2] = p2[cut1:cut2]
    for i in range(0, n):
        if p2[i] != -1:
            if not (p2[i] in c1) and not(cut1 <= i < cut2):
                c1[i] = p2[i]
            elif p2[i] in c1 and not(cut1 <= i < cut2):
                j = i
                while p2[j] in c1:
                    j = parent1.index(p2[j])
                c1[i] = parent2[j].copy()
            else:
                pass
    return c1


def OX(parent1, parent2):
    p1 = parent1.copy()
    p2 = parent2.copy()
    res = [-1]*len(parent1)
    r1, r2 = [random.randint(0, len(parent1) - 1) for i in range(2)]
    if r1 > r2:
        r1, r2 = r2, r1
    res[r1:r2] = p1[r1:r2]

    for item in p1[r1:r2]:
        index = p2.index(item)
        p2.pop(index)

    for item in p2:
        index = res.index(-1)
        res[index] = item

    testSequence(res)
    return res


def smartCross(p1, p2) -> List[int]:
    p1.getBadWorks()
    p2.getBadWorks()
    block_time1 = p1.idxSequence.index(p2.badWorks[0]) if p1.badWorks else random.randint(0, len(p1)-1)
    block_time2 = p2.idxSequence.index(p2.badWorks[0]) if p2.badWorks else random.randint(0, len(p2)-1)
    seq1 = p1.idxSequence.copy()
    seq2 = p2.idxSequence.copy()
    res = [-1]*len(seq1)

    if block_time1 < block_time2:
        seq1, seq2 = seq2, seq1
    res[0: block_time1] = seq1[0: block_time1]

    for item in res[0: block_time1]:
        index = seq2.index(item)
        seq2.pop(index)

    for item in seq2:
        index = res.index(-1)
        res[index] = item

    testSequence(res)
    return res

def countNeibs(p1, p2, p3, number):
    neibs = []
    index1 = p1.index(number)
    index2 = p2.index(number)
    if index1 == len(p1)-1:
        if p1[0] not in neibs: neibs.append(p1[0])
    else:
        if p1[index1+1] not in neibs: neibs.append(p1[index1+1])
    if p1[index1-1] not in neibs: neibs.append(p1[index1-1])

    if index2 == len(p2)-1:
        if p2[0] not in neibs: neibs.append(p2[0])
    else:
        if p2[index2+1] not in neibs: neibs.append(p2[index2+1])
    if p2[index2-1] not in neibs: neibs.append(p2[index2-1])

    return neibs
    

def ERX(p1, p2) -> List[int]:
    res = [-1]*len(p1)
    neibs = []
    res[0] = p1[0]
    while True:
        neibs = []
        try:
            index = res.index(-1) - 1
        except ValueError:
            break

        number = res[index]
        neibs = countNeibs(p1, p2, res, number)
        neibs2 = []
        for item in neibs:
            neibs2.append(len(countNeibs(p1, p2, res, item)))

        for item in res:
            if item in neibs:
                index3 = neibs.index(item)
                neibs.pop(index3)
                neibs2.pop(index3)

        if neibs2:
            index3 = neibs2.index(min(neibs2))
            res[index+1]=neibs[index3]
        else:
            notInRes = []
            for item in p1:
                if item not in res: notInRes.append(item)
            res[index+1] = random.choice(notInRes)
        
    testSequence(res)
    return res

if __name__ == "__main__":        
   print('ERX',ERX([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], [3, 5, 6, 8, 4, 2, 1, 7, 10, 11, 9, 15, 14, 13, 12]))
