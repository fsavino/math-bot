#!/usr/bin/python3.6
"""Defines commands used for the Memers server."""
import json
import random
import asyncio
import discord
from discord.ext import commands
import config

MAX_VOTES = 10

def check_votes(user):
    """Checks if a user is banned from submitting."""
    with open(f"./resources/votes.json", "r+") as vote_file:
        votes = json.load(vote_file)
    if user in votes:
        votes_left = MAX_VOTES - len(votes[user])
    else:
        votes_left = MAX_VOTES
    return votes_left > 0

def add_to_json(filename, call, response, user, is_img):
    """Adds a record to the given json file."""
    with open(f"./resources/{filename}", "r+") as response_file:
        responses = json.load(response_file)
    can_submit = check_votes(user)
    if can_submit:
        if call in responses:
            out_msg = "This call already exists. Please use a different one."
        else:
            responses[call] = {}
            responses[call]["response"] = response
            responses[call]["user"] = user
            with open(f"./resources/{filename}", "w") as response_file:
                json.dump(responses, response_file)
            if not is_img:
                out_msg = f"{user} added call/response pair '{call}' -> '{response}'!"
            else:
                out_msg = f"{user} added image call/response pair {call} -> <{response}>!"
    else:
        out_msg = "You are banned from submitting."
    return out_msg

def remove_from_json(filename, call):
    """Removes the given record from the given json file."""
    with open(f"./resources/{filename}", "r+") as response_file:
        responses = json.load(response_file)
    if call in responses:
        response = responses[call]["response"]
        user = responses[call]["user"]
        responses.pop(call)
        with open(f"./resources/{filename}", "w") as response_file:
            json.dump(responses, response_file)
        return (response, user)
    return (None, None)

def list_from_json(filename, is_img):
    """Lists all records from the given json file."""
    out_msg = "Call -> Response\n"
    with open(f"./resources/{filename}", "r+") as response_file:
        responses = json.load(response_file)
        for call, response_dict in responses.items():
            response = response_dict["response"]
            user = response_dict["user"]
            if not is_img:
                out_msg += f"{call} -> {response}, by {user}\n"
            else:
                out_msg += f"{call}\n"
    out_msg = f"```{out_msg}```"
    return out_msg

def list_user_adds(filename, user, is_img):
    """Lists all adds by a user."""
    out_msg = "Call -> Response\n"
    with open(f"./resources/{filename}", "r+") as response_file:
        responses = json.load(response_file)
        for call, response_dict in responses.items():
            response = response_dict["response"]
            sub_user = response_dict["user"]
            if user == sub_user:
                if not is_img:
                    out_msg += f"{call} -> {response}\n"
                else:
                    out_msg += f"{call}\n"
    if out_msg == "Call -> Response\n":
        out_msg = f"Nothing submitted by {user}."
    out_msg = f"```{out_msg}```"
    return out_msg

class Memers():
    """Defines the cap command and functions."""

    def __init__(self, bot):
        self.bot = bot
        self.bot.victim = ""
        self.bot.victim_choice = self.bot.loop.create_task(self.choose_victim())
        self.bot.pct = 0.10
        self.bot.max_votes = MAX_VOTES

    @commands.group()
    async def cool(self, ctx):
        """Says if a user is cool.
        In reality this just checks if a subcommand is being invoked.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send('No, {0.subcommand_passed} is not cool'.format(ctx))

    @cool.command(name='bot')
    async def _bot(self, ctx):
        """Is the bot cool?"""
        await ctx.send('Yes, the bot is cool.')

    @commands.command()
    async def markdonalds(self, ctx):
        """Lets the command markdonalds return the mRage emoji."""
        mrage = self.bot.get_emoji(413441118102093824)
        await ctx.send(f"{mrage}")

    @commands.command()
    # @commands.is_owner()
    async def add(self, ctx, call, response):
        """Adds a new call/response pair. Bad additions will get your privileges revoked."""
        filename = "responses.json"
        user = ctx.author.name
        out_msg = add_to_json(filename, call, response, user, False)
        await ctx.send(out_msg)

    @commands.command(name="rm", hidden=True)
    @commands.is_owner()
    async def remove(self, ctx, call):
        """Removes a call/response pair. Bot owner only!"""
        filename = "responses.json"
        (user, response) = remove_from_json(filename, call)
        if response is not None:
            out_msg = f"Removed {user}'s text call/response pair '{call}' -> '{response}'!"
        else:
            out_msg = f"Text call '{call}' not found."
        await ctx.author.send(out_msg)

    @commands.command()
    async def calls(self, ctx):
        """Lists the existing call/responses pairs."""
        filename = "responses.json"
        out_msg = list_from_json(filename, False)
        await ctx.author.send(out_msg)

    @commands.command()
    async def blame(self, ctx, user):
        """Lists all added pairs by a given user."""
        filename = "responses.json"
        out_msg = list_user_adds(filename, user, False)
        await ctx.author.send(out_msg)

    @commands.group(invoke_without_command=True)
    async def img(self, ctx, call):
        """Provides the parser for image call/response commands."""
        # if ctx.invoked_subcommand is None and ctx.channel.id != config.main_channel:
        if ctx.invoked_subcommand is None:
            with open(f"./resources/image_responses.json", "r+") as response_file:
                responses = json.load(response_file)
                try:
                    found_url = responses[call]['response']
                    image_embed = discord.Embed()
                    image_embed.set_image(url=found_url)
                    await ctx.send(content=None, embed=image_embed)
                except KeyError:
                    print("No response in file!")

    @img.command(name="add")
    # @commands.is_owner()
    async def _add(self, ctx, call, image_url):
        """Adds a new image response."""
        filename = "image_responses.json"
        user = ctx.author.name
        out_msg = add_to_json(filename, call, image_url, user, True)
        await ctx.send(out_msg)

    @img.command(name="rm")
    @commands.is_owner()
    async def _remove(self, ctx, call):
        """Removes an image response. Bot owner only!"""
        filename = "image_responses.json"
        image_url = remove_from_json(filename, call)
        if image_url is not None:
            out_msg = f"Removed image call/response pair {call} -> <{image_url}>!"
        else:
            out_msg = f"Image call {call} not found."
        await ctx.author.send(out_msg)

    @img.command(name="calls")
    async def _calls(self, ctx):
        """Lists the existing image call/responses pairs."""
        filename = "image_responses.json"
        out_msg = list_from_json(filename, True)
        await ctx.author.send(out_msg)

    @img.command(name="blame")
    async def _blame(self, ctx, user):
        """Lists all added pairs by a given user."""
        filename = "image_responses.json"
        out_msg = list_user_adds(filename, user, True)
        await ctx.author.send(out_msg)

    @commands.command()
    async def voteban(self, ctx, user):
        """Votes to disallow a user from adding images or text calls."""
        filename = "votes.json"
        try:
            with open(f"./resources/{filename}", "r+") as vote_file:
                votes = json.load(vote_file)
        except FileNotFoundError:
            with open(f"./resources/{filename}", "w+") as vote_file:
                json.dump({}, vote_file)
            votes = {}
        voter = ctx.author.name
        if user in votes:
            votes_against = votes[user]
            if voter in votes_against:
                await ctx.author.send(f"You have already voted against {user}!")
            else:
                votes_against.append(voter)
                votes[user] = votes_against
                num_votes_left = self.bot.max_votes-len(votes_against)
                await ctx.send(f"You have voted against {user}. "
                               f"{num_votes_left} more votes until submission ban.")
        else:
            votes[user] = [voter]
            num_votes_left = self.bot.max_votes-1
            await ctx.send(f"You have voted against {user}. "
                           f"{num_votes_left} more votes until submission ban.")
        with open(f"./resources/{filename}", "w") as vote_file:
            json.dump(votes, vote_file)

    @commands.command()
    async def votes(self, ctx, user):
        """Displays the current number of votes against a user."""
        filename = "votes.json"
        with open(f"./resources/{filename}", "r+") as vote_file:
            votes = json.load(vote_file)
        if user in votes:
            num_votes_left = self.bot.max_votes-len(votes[user])
            await ctx.send(f"{user} has {num_votes_left} more votes until submission ban.")
        else:
            num_votes_left = self.bot.max_votes
            await ctx.send(f"{user} has {num_votes_left} more votes until submission ban.")

    @commands.command()
    @commands.is_owner()
    async def clearvotes(self, ctx, user):
        """Clears votes against a player, effectively unbanning them."""
        filename = "votes.json"
        with open(f"./resources/{filename}", "r+") as vote_file:
            votes = json.load(vote_file)
        votes[user] = []
        await ctx.send(f"Cleared votes for {user}.")
        with open(f"./resources/{filename}", "w") as vote_file:
            json.dump(votes, vote_file)

    @commands.command()
    @commands.is_owner()
    async def player(self, ctx, player):
        """Sets a new player victim. Bot owner only!"""
        self.bot.victim = player
        await ctx.send(f"New victim chosen: {self.bot.victim}")

    @commands.command()
    @commands.is_owner()
    async def pct(self, ctx, pct):
        """Sets the chance that the bot adds a random reaction."""
        self.bot.pct = float(pct)/100.0
        await ctx.send(f"New reaction percentage chosen: {self.bot.pct}")

    async def choose_victim(self):
        """Chooses a victim to add reactions to."""
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            guild_members = self.bot.get_guild(config.guild_id).members
            victim_member = random.sample(guild_members, 1)[0]
            self.bot.victim = victim_member.name
            print(f"New victim: {self.bot.victim}")
            await asyncio.sleep(10000)

    async def on_message(self, ctx):
        """Defines on_message behavior for responses and victim reaction adding."""
        if ctx.author.bot:
            return

        reaction_pct = random.random()
        if self.bot.victim == ctx.author.name and reaction_pct < self.bot.pct:
            add_emoji = random.sample(self.bot.emojis, 1)[0]
            await ctx.add_reaction(add_emoji)

        # if ctx.channel.id != config.main_channel:
        if not ctx.content.startswith("$"):
            with open(f"./resources/responses.json", "r+") as response_file:
                responses = json.load(response_file)
                try:
                    for call, response_dict in responses.items():
                        response = response_dict['response']
                        if call in ctx.content.lower():
                            await ctx.channel.send(f"{response}")
                except KeyError:
                    print("No response in file!")

        if ctx.channel.id != config.main_channel:
            if ctx.content.lower() in ["i'm dad", "im dad"]:
                await ctx.channel.send(f"No you're not, you're {ctx.author.mention}.")

            elif "i'm " in ctx.content.lower():
                imindex = ctx.content.lower().index("i'm") + 4
                await ctx.channel.send(f"Hi {ctx.content[imindex:]}, I'm Dad!")

        if ctx.content.lower() == "out":
            await ctx.channel.send(f":point_right: :door: :rage:")

        if ctx.content.lower() == "in":
            await ctx.channel.send(f":grinning: :door: :point_left:")

def setup(bot):
    """Adds the cog to the bot."""
    bot.add_cog(Memers(bot))

        # schep_questions = ["does schep have tess", "did schep get tess", "does schep have tess yet"]
        # milow_questions = ["does milow have ace", "did milow get ace", "does milow have ace yet"]
        # if (content.lower() in schep_questions) or (content.lower()[:-1] in schep_questions):
        #     schep_has_tess = SESSION.query(
        #         HasTess.has_tess).filter(HasTess.name == "Schep").first()
        #     if schep_has_tess is None or schep_has_tess[0] is False:
        #         await channel.send(f"Schep does not have Tess, make sure to let him know ;)", tts=True)
        #     else:
        #         await channel.send(f"Schep finally got Tess!")

        # elif (content.lower() in milow_questions) or (content.lower()[:-1] in milow_questions):
        #     schep_has_tess = SESSION.query(
        #         HasTess.has_tess).filter(HasTess.name == "Milow").first()
        #     if schep_has_tess is None or schep_has_tess[0] is False:
        #         await channel.send(f"Milow does not have Ace.", tts=True)
        #     else:
        #         await channel.send(f"Milow finally got Ace!")
