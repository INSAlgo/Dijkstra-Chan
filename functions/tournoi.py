#!/usr/bin/env python3

import itertools
import os
import sys
import pathlib
import subprocess
import argparse
import asyncio
import random
import time
import discord
from bot import bot

from commands import p4

MAX_PARALLEL_PROCESSES = 10
ALLOWED_EXTENSIONS = ('.py', '.js', '', '.out', '.class')

class Progress():

    def __init__(self):
        self.nb_games: int
        self.game_nb = 0
        self.start_time = time.time()
        self.message: discord.Message

    def log_results(self, log, players, winner, errors):
        self.game_nb += 1
        print(f"{self.game_nb}.",
              f"{' vs '.join(display_name(player) for player in players)} ->",
              f"{display_name(winner) if winner else 'draw'}",
              sep = " ", end = "", file=log)
        if errors:
            print(f" ({', '.join(f'{display_name(player)}: {error}' for player, error in errors.items())})", file=log)
        else:
            print(file=log)

    async def first_message(self, ctx):
        self.message = await ctx.send("0%")

    async def update_message(self):
        if self.game_nb % 30 == 0:
            await self.message.edit(content=f"{round(self.game_nb / self.nb_games * 100)}%" +
                                    f" ({round(time.time() - self.start_time)}s)")

def explore(out_dir):
    ai_paths = list()
    for root, _, files in os.walk(out_dir):
        for file in files:
            ai_path = pathlib.Path(root) / file
            if ai_path.suffix in ALLOWED_EXTENSIONS and not ai_path.stem.startswith("."):
                ai_paths.append(ai_path)
    return ai_paths

def display_name(player):
    return bot.client.get_user(int(player.name)).display_name

async def safe_game(game, semaphore, log, progress: Progress, players, args):
    async with semaphore:
        players, winner, errors = await game.module.main(list(players) + args, discord=True)
        progress.log_results(log, players, winner, errors)
        await progress.update_message()
        return players, winner

def make(game, *args):
    args = *("make", "--directory", str(game.game_dir)), *args
    subprocess.run(args, capture_output=True)

async def tournament(ctx, game, rematches, nb_players, src_dir, args):

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

    log_file = game.log_file.open("w")
    progress = Progress()

    for combinations in itertools.combinations(map(str, ai_files), nb_players):
        for players in itertools.permutations(combinations):
            for _ in range(rematches):
                games.append(safe_game(game, semaphore, log_file, progress, players, args))

    progress.nb_games = len(games)
    random.shuffle(games)
    
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
    make(game, "clean")

    return scoreboard

async def main(ctx, game, raw_args=None):

    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rematches", type=int, default=1, metavar="NB_REMATCHES")
    parser.add_argument("-p", "--players", type=int, default=2, metavar="NB_PLAYERS")
    parser.add_argument("-d", "--directory", default=p4.AI_DIR_NAME, metavar="SRC_DIRECTORY")

    args, remaining_args = parser.parse_known_args(raw_args)
    src_dir = game.game_dir / args.directory

    return await tournament(ctx, game, args.rematches, args.players, src_dir, remaining_args)
