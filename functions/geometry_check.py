import numpy as np

def orient(p, q, r):
    mat = [
        [1, p[0], p[1]],
        [1, q[0], q[1]],
        [1, r[0], r[1]]
    ]
    return np.sign(np.linalg.det(mat))

def is_clockwise(CH: list[tuple[int]]) -> bool :
    i = CH.index(min(CH))
    n = len(CH)
    return orient(CH[(i-1)%n], CH[i], CH[(i+1)%n]) <= 0

def is_convex(CH: list[tuple[int]]) -> bool :
    n = len(CH)
    for i in range(n):
        if orient(CH[i], CH[(i+1)%n], CH[(i+2)%n]) > 0 :
            return False
    return True

def is_hull(S: list[tuple[int]], CH: list[tuple[int]]) -> bool :
    h = len(CH)
    for p in S:
        for i in range(h):
            if orient(CH[i], CH[(i + 1)%h], p) > 0 :
                return False
    return True


def check(S: list[tuple[int]], CH: list[tuple[int]], ex_type: str = "points") -> str :

    if not is_clockwise(CH):
        CH.reverse()
    
    message: list[str] = []
    mistake = False

    if set(CH).issubset(set(S)) :
        if ex_type == "points" :
            message.append("The hull is made of the points given. :white_check_mark:")
        else :
            message.append("The hull is made of the polygon's points. :white_check_mark:")
    else :
        mistake = True
        if ex_type == "points" :
            message.append("The hull is made of points that were not given! <:ah:737340475866087526> :x:")
        else :
            message.append("The hull is made of points that are not part of the polygon! <:ah:737340475866087526> :x:")
    
    if is_convex(CH) and not mistake :
        message.append("The hull is convex. :white_check_mark:")
    elif not mistake :
        mistake = True
        message.append("The hull is not convex! <:oof:762676683546689556> :x:")
    
    if is_hull(S, CH) and not mistake :
        if ex_type == "points" :
            message.append("The hull contains all the points. :white_check_mark:")
        else :
            message.append("The hull contains all the polygon's points. :white_check_mark:")
    elif not mistake :
        mistake = True
        if ex_type == "points" :
            message.append("The hull does not contains all the points! <:chonteux:722130313979101314> :x:")
        else :
            message.append("The hull does not contains all the polygon's points! <:chonteux:722130313979101314> :x:")

    if mistake :
        message.append("Incorrect solution. <:sad_cat:737953393816895549> :x:")
    else :
        message.append("Perfect solution! <:feelsgood:737960024390762568> :white_check_mark:")
    
    return '\n'.join(message)