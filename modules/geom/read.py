import matplotlib.pyplot as plt

def plot_point(x: int, y: int, col: str = 'k'):
    plt.plot(x, y, color=col, marker='.')

def plot_segment(p1: tuple[int], p2: tuple[int], col: str = 'k'):
    x1, y1 = p1
    x2, y2 = p2
    plt.plot([x1, x2], [y1, y2], color=col)
    plot_point(x1, y1, col)
    plot_point(x2, y2, col)

def plot_polygon(P: list[tuple[int]], col: str = 'k'):
    for i in range(len(P)):
        plot_segment(P[i], P[(i + 1) % len(P)], col)

def draw_submission(raw_submission: str, ex_type: str = "points") -> tuple[int, str | tuple[list[tuple[int]]]] :
    """
    Draws the submission and returns the list of points of the scatter/polygon and the list of points of the convex hull
    raw_submission : the raw text given
    ex_type : the type of the submission : "polygon" for exercise 4, "points" for other exercises
    """

    # Checking general info about the submission
    for c in raw_submission:
        if c not in [' ', '\r', '\n', '-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] :
            return 1, f"unauthorized character : {c}"
    
    lines = raw_submission.split('\n')
    while lines[-1] == '':
        lines.pop()
    
    N = len(lines)
    
    lengths = [len(line.split(' ')) for line in lines]

    if not lengths:
        return 1, "empty answer"
    

    # Reading points/the polygon
    if lengths[0] != 1:
        return 1, "invalid n"
    n = int(lines[0])
    if N-2 < n:
        return 1, f"not enough lines to read {ex_type} : expected {n}, found only {N-2}"
    
    P = []
    for i in range(n):
        if lengths[i+1] != 2:
            return 1, f"line {i+1} is invalid"
        x, y = map(int, lines[i+1].split(' '))
        P.append((x, y))
        if ex_type == "points" :
            plot_point(x, y)
    if ex_type == "polygon" :
        plot_polygon(P)
    
    
    # Reading the hull
    if lengths[n+1] != 1:
        return 1, "invalid h"
    h = int(lines[n+1])
    if N-n-2 < h :
        return 1, f"not enough lines to read convex hull : expected {h}, found only {N-n-2}"
    
    CH = []
    for i in range(h):
        if lengths[n+i+2] != 2:
            return 1, f"line {n+i+1} is invalid"
        x, y = map(int, lines[n+i+2].split(' '))
        CH.append((x, y))
    plot_polygon(CH, col='r')


    # Saving the plot as "temp.png"
    plt.axis("equal")
    plt.savefig("temp.png")
    plt.clf()
    
    return 0, (P, CH)