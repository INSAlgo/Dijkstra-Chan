#!/usr/bin/env python3

import asyncio, itertools, os, sys
from argparse import ArgumentParser, REMAINDER
from pathlib import Path
from subprocess import run
from time import time as t
from random import shuffle

import discord

from modules.game.game_classes import AvailableGame

MAX_PARALLEL_PROCESSES = 1
ALLOWED_EXTENSIONS = ('.py', '.js', '', '.out', '.class')

class Progress():

    def __init__(self):
        self.nb_games: int
        self.game_nb = 0
        self.start_time = t()
        self.message: discord.Message

    def log_results(self, bot, log, players, winner, errors):
        self.game_nb += 1
        print(f"{self.game_nb}.",
              f"{' vs '.join(display_name(bot, player) for player in players)} ->",
              f"{display_name(bot, winner) if winner else 'draw'}",
              sep = " ", end = "", file=log)
        errors = {player: error for player, error in errors.items() if error}
        if errors:
            print(f" ({', '.join(f'{display_name(bot, player)}: {error}' for player, error in errors.items())})", file=log)
        else:
            print(file=log)

    async def first_message(self, ctx):
        self.message = await ctx.send("0%")

    async def update_message(self):
        if self.game_nb % 30 == 0 and self.nb_games != 0:
            await self.message.edit(content=f"{round(self.game_nb / self.nb_games * 100)}%" +
                                    f" ({round(t() - self.start_time)}s)")

def explore(out_dir):
    ai_paths = list()
    for root, _, files in os.walk(out_dir):
        for file in files:
            ai_path = Path(root) / file
            if ai_path.suffix in ALLOWED_EXTENSIONS and not ai_path.stem.startswith("."):
                ai_paths.append(ai_path)
    return ai_paths

def display_name(bot, player):
    if isinstance(player, str):
        return player

    user = bot.get_user(int(player.name))
    assert user
    return user.display_name

async def safe_game(game, semaphore, bot, log, progress: Progress, players, args):
    async with semaphore:
        try:
            players, winner, errors = await game.module.main(list(players) + args, discord=True)
        except SystemExit as e:
            # Wrong arguments
            players = [bot.get_user(int(player.split("_")[1].split('.')[0])).name for player in players]
            winner, errors = None, {player: "SystemExit" for player in players}

        progress.log_results(bot, log, players, winner, errors)
        await progress.update_message()
        return players, winner

def make(game, *args):
    return # DO NOT USE, MAKEFILE IS NOT WORKING ANYMORE
    args = *("make", "--directory", str(game.game_path)), *args
    run(args, capture_output=True)

async def tournament(ctx, game, nb_players, src_dir, args, games_args=None):

    await ctx.channel.send(content=f"Starting **{game.name}** tournament")

    # # Compile programs -> no don't
    # make(game, f"SRCDIR={src_dir.name}")
    # await ctx.channel.send("Compilation done" )

    # Get all programs
    out_dir: Path = game.ai_path
    ai_files = explore(out_dir)

    # Initialize score
    scores = {}
    for ai_file in ai_files:
        name = ai_file.stem
        if name.startswith("ai_"):
            name = name[3:]
        scores[name] = 0

    # Create list of coroutines to run
    games = list()
    semaphore = asyncio.Semaphore(MAX_PARALLEL_PROCESSES)

    log_file = game.log_file.open("w")
    progress = Progress()
    if not games_args:
        games_args = [""]

    for combinations in itertools.combinations(map(str, ai_files), nb_players): # All combinations of players
        for players in itertools.permutations(combinations): # Each starting configuration
            for current_args in games_args:
                if isinstance(current_args, str):
                    current_args = current_args.split()
                games.append(safe_game(game, semaphore, ctx.bot, log_file, progress, players, args + current_args))

    progress.nb_games = len(games)
    shuffle(games)

    await ctx.channel.send(f"Running **{progress.nb_games}** games between **{len(ai_files)}** AI")
    await progress.first_message(ctx)

    origin_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")
    try:
        results = await asyncio.gather(*games)
    except KeyboardInterrupt as exception:
        make(game, "clean")
        raise exception
    sys.stdout = origin_stdout
    log_file.close()

    await progress.update_message()

    # Awaiting and printing results
    for players, winner in results:
        if winner:
            scores[winner.name] += 1

    scoreboard = sorted(scores.items(), key=lambda score: score[1], reverse=True)
    # make(game, "clean") # big mistake

    return scoreboard

async def main(ctx, game, raw_args=None) -> list[tuple]:

    parser = ArgumentParser()
    parser.add_argument("-p", "--players", type=int, default=2, metavar="NB_PLAYERS")
    parser.add_argument("-d", "--directory", default=AvailableGame.UPLOAD_DIR_NAME, metavar="SRC_DIRECTORY")
    parser.add_argument("-g", "--games_args", nargs=REMAINDER, metavar="ARGS", default=[])

    try:
        args, remaining_args = parser.parse_known_args(raw_args)
    except SystemExit:
        return None
    src_dir = game.game_path / args.directory

    return await tournament(ctx, game, args.players, src_dir, remaining_args, args.games_args)
