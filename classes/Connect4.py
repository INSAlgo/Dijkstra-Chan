import sys
from abc import ABC, abstractmethod
from os import path
import pexpect

WIDTH = 7
HEIGHT = 6
TIMEOUT = 0.1


class Player(ABC):

    def __init__(self):
        pass

    @abstractmethod
    def startGame(self, no, size):
        self.no = no

    @abstractmethod
    def askMove(self, verbose):
        pass

    @abstractmethod
    def tellLastMove(self, x):
        pass

class User(Player):

    def __init__(self):
        super().__init__()

    def startGame(self, no, size):
        return super().startGame(no, size)

    def askMove(self, verbose):
        if verbose:
            print(f"Column for player {self.no} : ", end="")
        try:
            return input()
        except KeyboardInterrupt:
            sys.exit(1)

    def tellLastMove(self, x):
        return super().tellLastMove(x)

    def __str__(self):
        return f"Player {self.no}"

class AI(Player):

    @staticmethod
    def command(progName):
        if not path.exists(progName):
            sys.stderr.write(f"File {progName} not found\n")
            sys.exit(1)
        extension = progName.split(".")[-1]
        match extension:
            case "py":
                return f"python ./C4_AIs/{progName}"
            case "js":
                return f"node ./C4_AIs/{progName}"
            case _:
                return f"./C4_AIs/{progName}"

    def __init__(self, progPath):
        super().__init__()
        self.progPath = progPath
        self.progName = path.basename(progPath)

    def startGame(self, no, size):
        super().startGame(no, size)
        self.prog = pexpect.spawn(AI.command(self.progPath), timeout=TIMEOUT)
        self.prog.delaybeforesend = None
        self.prog.setecho(False)
        start = 2 - self.no
        self.prog.sendline(f"{size[0]} {size[1]} {start}")

    def askMove(self, verbose):
        if verbose:
            print(f"Column for {self} : ", end="")
        try:
            progInput = self.prog.readline().decode('ascii').strip()
        except pexpect.TIMEOUT:
            print("Program 1 took too long")
            return False
        if verbose:
            print(progInput)
        return progInput

    def tellLastMove(self, x):
        self.prog.sendline(str(x))

    def __str__(self):
        return f"AI {self.no} ({self.progName})"

class Game :
    def __init__(self, width=WIDTH, height=HEIGHT, verbose=False) -> None:
        self.board = [[0 for _ in range(height)] for _ in range(width)]
        self.verbose = verbose
        self.size = (width, height)
        self.players = [Player(), Player()]
        self.logs = []
    
    def checkWin(self, no):
        for x in range(WIDTH):
            for y in range(HEIGHT):
                if self.board[x][y] == no:
                    for dx, dy in ((1, 0), (0, 1), (1, 1), (1, -1)):
                        streak = 1
                        for i in range(1, 4):
                            nx, ny = x + dx * i, y + dy * i
                            if nx >= WIDTH or ny >= HEIGHT:
                                break
                            if self.board[nx][ny] == no:
                                streak += 1
                            else:
                                break
                        if streak >= 4:
                            return True
        return False

    def log(self, player_name: str, move: int) :
        self.logs.append(f"player {player_name} played on column {move}")
        self.logs.append()

    def display(self) :
        pass

    def play(self) :
        self.players[0].startGame(1, self.size)
        self.players[1].startGame(2, self.size)
        turn = 0
        winner = None

        while winner is None:
            turn += 1
            player = self.players[(turn + 1)% 2]
            otherPlayer = self.players[turn % 2]
            if self.verbose:
                display(self.board)
            userInput = False
            while not userInput:
                userInput = player.askMove(self.verbose)
                userInput = sanithize(self.board, userInput, self.verbose)
                if not userInput and isinstance(player, AI):
                    if self.verbose:
                        return winMessage(otherPlayer)
                    elif isinstance(player, AI):
                        return player.progName
            x, y = userInput
            y = fallHeight(board, x)
            self.board[x][y] = player.no
            otherPlayer.tellLastMove(x)
            if checkWin(self.board, player.no):
                if self.verbose:
                    display(self.board)
                    return winMessage(otherPlayer)
                elif isinstance(player, AI):
                    return player.progName

class AI_AI_Game (Game) :
    def __init__(self, p_name1: str, p_name2: str, width=WIDTH, height=HEIGHT, verbose=False) -> None:
        super().__init__(width, height, verbose)
        self.players = [AI(p_name1), AI(p_name2)]

class AI_User_Game (Game) :
    def __init__(self, p_name1: str, p_name2: str, width=WIDTH, height=HEIGHT, verbose=False) -> None:
        super().__init__(width, height, verbose)
        if p_name1.startswith("AI:") :
            self.players = [AI(p_name1[3:]), User(p_name2)]
        else :
            self.players = [User(p_name1), AI(p_name2[3:])]

