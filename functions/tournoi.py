#!/usr/bin/env python3

import itertools
import os
import sys
import pathlib
import subprocess
import argparse
import asyncio
import random
from discord import Message

from discord.ext.commands import Bot

from commands import p4


MAX_PARALLEL_PROCESSES = 200
ALLOWED_EXTENSIONS = ('.py', '.js', '', '.out', '.class')

class Progress():
    nb_games: int
    message: Message

    def __init__(self):
        self.game_nb = 0

# Globals
game_nb: int

def explore(out_dir):
    ai_paths = list()
    for root, _, files in os.walk(out_dir):
        for file in files:
            ai_path = pathlib.Path(root) / file
            if ai_path.suffix in ALLOWED_EXTENSIONS and not ai_path.stem.startswith("."):
                ai_paths.append(ai_path)
    return ai_paths

def display_name(bot, player):
    return bot.get_user(int(player.name)).display_name

def print_game_results(bot: Bot, progress, players, winner, errors):
    print(f"{progress.game_nb}.",
          f"{' vs '.join(display_name(bot, player) for player in players)} ->",
          f"{display_name(bot, winner) if winner else 'draw'}",
          sep = " ", end = "")
    if errors:
        print(f" ({', '.join(f'{display_name(bot, player)}: {error}' for player, error in errors.items())})")
    else:
        print()

async def safe_game(bot, game, semaphore, devnull, origin_stdout, progress: Progress, players, args):
    async with semaphore:
        players, winner, errors = await game.module.main(list(players) + args, discord=True)
        progress.game_nb += 1
        sys.stdout = origin_stdout
        print_game_results(bot, progress, players, winner, errors)
        sys.stdout = devnull
        if progress.game_nb % 20 == 0:
            await progress.message.edit(content=f"{round(progress.game_nb / progress.nb_games * 100)}%")
        return players, winner

def make(game, *args):
    args = *("make", "--directory", str(game.game_dir)), *args
    subprocess.run(args, capture_output=True)

async def tournament(bot, ctx, game, rematches, nb_players, src_dir, args):

    await ctx.channel.send(content=f"Starting **{game.name}** tournament")

    # Compile programs
    make(game, f"SRCDIR={src_dir.name}")
    await ctx.channel.send(f"Compilation done" )

    # Get all programs
    out_dir: pathlib.Path = game.game_dir / "out"
    ai_files = explore(out_dir)

    # Initialize score
    scores = {ai_file.stem : 0 for ai_file in ai_files}

    # Create list of coroutines to run
    games = list()
    semaphore = asyncio.Semaphore(MAX_PARALLEL_PROCESSES)

    origin_stdout = sys.stdout
    devnull = open(os.devnull, "w")
    sys.stdout = devnull

    progress = Progress()
    for combinations in itertools.combinations(map(str, ai_files), nb_players):
        for players in itertools.permutations(combinations):
            for _ in range(rematches):
                games.append(safe_game(bot, game, semaphore, devnull, origin_stdout, progress, players, args))

    progress.nb_games = len(games)
    await ctx.channel.send(f"Running **{progress.nb_games}** games between **{len(ai_files)}** AI")

    progress.message = await ctx.channel.send(f"0%")
    random.shuffle(games)

    try:
        results = await asyncio.gather(*games)
    except KeyboardInterrupt as exception:
        make(game, "clean")
        raise exception

    await progress.message.edit(content="100%")

    # Awaiting and printing results
    for players, winner in results:
        if winner:
            scores[winner.name] += 1
    sys.stdout = origin_stdout

    scoreboard = sorted(scores.items(), key=lambda score: score[1], reverse=True)
    make(game, "clean")

    return scoreboard

async def main(bot, ctx, game, raw_args=None):

    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rematches", type=int, default=1, metavar="NB_REMATCHES")
    parser.add_argument("-p", "--players", type=int, default=2, metavar="NB_PLAYERS")
    parser.add_argument("-d", "--directory", default=p4.AI_DIR_NAME, metavar="SRC_DIRECTORY")

    args, remaining_args = parser.parse_known_args(raw_args)
    src_dir = game.game_dir / args.directory

    return await tournament(bot, ctx, game, args.rematches, args.players, src_dir, remaining_args)
