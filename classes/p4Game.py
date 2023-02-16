import discord
from discord.ext.commands import Bot

numbers = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:", ":keycap_ten:"]
pellets = [":black_large_square:", ":red_circle:", ":yellow_circle:", ":blue_circle:", ":green_circle:", ":orange_circle:", ":purple_circle:", ":brown_circle:", ":white_circle:"]

class Player :
    def __init__(self, type_: str, d_id: int, dm: discord.TextChannel = None) -> None:
        self.type = type_   # "User" or "AI"
        self.id = d_id      # discord id
        self.dm = dm        # dm channel to send on
        self.playing = True
    
    def get_name(self) -> str :
        if self.type == "User" :
            return f"<@{self.id}>"
        return f"AI of <@{self.id}>"

    async def send_result(self, text) :
        if self.type == "User" :
            await self.dm.send(text)

class P4Game :
    def __init__(self, id_, n_p, w, h, players: list[Player]) -> None:
        self.id = id_
        self.W, self.H = w, h
        self.N = n_p
        self.board = [[0 for _ in range(w)] for _ in range(h)]
        self.players = players
    
    def save_move(self, x: int, player: int) :
        y = self.H-1
        while y > 0 and self.board[y-1][x] == 0 :
            y -= 1
        
        self.board[y][x] = player
    
    def draw_board(self) :
        help_line = ' '.join(numbers[:self.W])
        emoji_board = [help_line]
        for line in self.board :
            emoji_line = []
            for cell in line :
                emoji = pellets[cell]
                emoji_line.append(emoji)
            emoji_board.append(' '.join(emoji_line))
        emoji_board.append(help_line)
        return '\n'.join(emoji_board[::-1])

    async def tell_move(self, move: int, p_n: int, p_j: int) :

        receiver = self.players[p_j-1]
        if receiver.type != "User" :
            return
        
        player = self.players[p_n-1]

        if move < 0 :
            if player.playing :
                await receiver.dm.send(f"{player.get_name()} was eliminated (timeout or illegal move).")
                player.playing = False
        else :
            await receiver.dm.send(f"{player.get_name()} played on column {move}.")
            self.save_move(move, p_n)

    async def ask_move(self, p_i: int, bot: Bot) -> str :
        player = self.players[p_i-1]
        if player.type != "User" :
            return "-1"
        
        await player.dm.send(self.draw_board() + f"\nYour turn {player.get_name()} (type `stop` to forfait) :")

        player_user = discord.User(id=player.id)
        while True :
            resp: discord.Message = await bot.wait_for(
                "message",
                check=lambda m: (m.channel == player.dm) and (m.author == player_user)
            )
            move_txt = resp.content
            if move_txt.lower() == "stop" :
                await player.dm.send("Okie Dokie !")
                return "stop"
            if move_txt in {str(i) for i in range(self.W)} :
                break
        
        move = int(move_txt)
        self.save_move(move, p_i)
        return move_txt

    async def send_results(self, text: str) :
        board_disp = self.draw_board()
        for player in self.players :
            await player.send_result(board_disp + '\n' + text)