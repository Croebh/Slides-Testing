import shlex
import discord
import re
from discord.ext import commands


# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/presentations'

# The ID of a sample presentation.
PRESENTATION_ID = '1iPbghn_hquZlwZDpKzOttonCl5tyF8809q8NJJOgT0w'

import functions

build = functions.GetPresentation(PRESENTATION_ID)
objects = functions.ObjectList(build)

bot = commands.Bot(command_prefix='~', description="Insert-Description")


@bot.event
async def on_message(message):
    global build
    global objects
    if message.author == bot.user:
        return
    if message.content == "Hello":
        await bot.send_message(message.channel, "World")
    await bot.process_commands(message)


@bot.command(pass_context=True)
async def exit(ctx):
    if ctx.message.author.id == Credentials().owner:
        await bot.add_reaction(ctx.message, '\u2705')
        await bot.logout()
    else:
        await bot.say("Error: You are not authorized to use this command")


@bot.command(name='pos', aliases=['position', 'p'])
async def pos(name: str):
    print('Getting coords for - '+name)
    combatant = objects.get_combatant(name)
    if combatant:
        await bot.say("{0.name} is at ({0.pos})".format(combatant))
    else:
        await bot.say('Error: No combatant found named {}'.format(name))


@bot.command(pass_context=True, aliases=['comp', 'distance'])
async def compass(ctx, name1, *, args=None):
    combatant1 = objects.get_combatant(name1)
    name2 = None
    quad = False
    if args:
        args = shlex.split(args)
        if len(args)>=2:
            name2 = args[0]
            quad = args[1]
        elif len(args) == 1:
            if str(args[0]).lower() in ["true", "quad", "quadrant"]:
                quad = True
            else:
                name2 = args[0]
    combatant2 = objects.get_combatant(name2)
    r = re.compile(r"(\d+)(?: ft.)")
    if combatant1 and not combatant2:
        embed = discord.Embed(title="{0.name} is at ({0.pos})".format(combatant1))
        out = {"North": [], "West": [], "South": [], "East": []}
        for other in objects.list:
            if other['objectId'] != combatant1.objectId:
                combatant2 = objects.get_combatant(other['name'])
                distance = functions.Distance(combatant1, combatant2)
                out[distance.quad].append("{0.name} is {1.ft} ft {1.compass} ({1.degree}°) at ({0.pos})".format(
                    combatant2, distance
                ))
        if quad:
            for i in out:
                if out[i]:
                    out[i].sort(key=lambda x :int(r.search(x).group(1)))
                    embed.add_field(name=i,value="\n".join(out[i]))
        else:
            outGroup = []
            for i in out:
                if out[i]:
                    outGroup += out[i]
            outGroup.sort(key=lambda x : int(r.search(x).group(1)))
            embed.description = "\n".join(outGroup)
        await bot.say(embed=embed)
    elif combatant1 and combatant2:
        distance = functions.Distance(combatant1, combatant2)
        embed = discord.Embed(title="{0.name} is at ({0.pos})".format(combatant1))
        embed.add_field(name="{0.name} is at ({0.pos})".format(combatant2),
                        value="{0.ft} ft. away, {0.compass} ({0.degree}°)".format(distance))
        await bot.say(embed=embed)


@bot.command(pass_context=True)
async def range(ctx, x, y:int, maxrange:int=None):
    if str(x).isalpha():
        x = x.upper()
        embed = discord.Embed(title="Distances from ({}, {})".format(x, y))
        x = functions.AlphConv(x.upper())
    else:
        embed = discord.Embed(title="Distances from ({}, {})".format(functions.AlphConv(int(x)), y))
    base = (int(x), int(y)  )
    out = []
    r = re.compile(r"(\d+)(?: ft.)")
    for i in objects.list:
        combatant = objects.get_combatant(i['name'])
        distance = functions.Distance(base,combatant)
        if maxrange:
            if distance.ft >= maxrange:
                continue
        out.append("{0.name} is {1.ft} ft. {1.compass} away at ({0.pos})".format(combatant, distance))
    if out:
        out.sort(key=lambda x :int(r.search(x).group(1)))
        out = '\n'.join(out)
    else:
        out = 'No combatants in range.'
    if maxrange:
        embed.title = embed.title + ', max range of {} ft.'.format(maxrange)
    embed.description = out
    await bot.say(embed=embed)

@bot.command()
async def get(name: str):
    combatant = objects.get_combatant(name)
    if combatant:
        await bot.say('{0.name} is a creature of {0.size} size, at coordinates ({0.pos}), and whose id is {0.objectId}'.format(
                                   combatant))
    else:
        await bot.say("Error: No combatant found named '{}'".format(name))


@bot.command(pass_context=True)
async def move(ctx, name, *, args):
    global build
    global objects
    args = shlex.split(args)  # `~move <name> <x> <y>`     Relative
    combatant = objects.get_combatant(name)  # Get combatant name `name`
    if args[0] == 'set':  # If Set, then use absolute
        abso = True
        x = args[1]
        y = int(args[2])
    else:  # Else Relative
        abso = False
        x = args[0]
        y = int(args[1])
    if combatant:  # If combatant found
        await bot.send_typing(ctx.message.channel)
        Move = functions.move(build, combatant, x, y, abso)  # Move combatant
        if Move.moving:
            await bot.change_presence(game=discord.Game(name="Updating..."))
            build = functions.GetPresentation(PRESENTATION_ID)  # Update Build
            objects = functions.ObjectList(build)  # Update Object List
            await bot.change_presence(game=discord.Game(name="Making a bot"))
        embed = discord.Embed(title="Moving {}".format(combatant.name))
        embed.add_field(name=Move.title, value=Move.message)
        await bot.say(embed=embed)  # Send move message
    else:  # Else Return Error
        await bot.say("Error: No combatant found named '{}'".format(name))


@bot.command(pass_context=True)
async def size(ctx):
    await bot.say("Size of the slide is {} Squares.".format(build.size))

@bot.command(pass_context=True, aliases=['update'])
async def refresh(ctx):
    global build
    global objects
    await bot.change_presence(game=discord.Game(name="Updating..."))
    await bot.send_typing(ctx.message.channel)
    build = functions.GetPresentation(PRESENTATION_ID)  # Update Build
    objects = functions.ObjectList(build)  # Update Object List
    await bot.say('Updated!')
    await bot.change_presence(game=discord.Game(name="Making a bot"))


# @bot.event
# async def on_command_error(error, ctx):
#     channel = ctx.message.channel
#     if isinstance(error, commands.MissingRequiredArgument):
#         await send_cmd_help(ctx)
#     elif isinstance(error, commands.BadArgument):
#         await send_cmd_help(ctx)
#     elif isinstance(error, commands.CommandInvokeError):
#         print("Exception in command '{}', {}".format(ctx.command.qualified_name, error.original))
#         traceback.print_tb(error.original.__traceback__)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(game=discord.Game(name="Making a bot"))


class Credentials:
    def __init__(self):
        try:
            import credentials
        except ImportError:
            raise Exception("Credentials not found.")
        self.token = credentials.token
        self.owner = credentials.owner


bot.run(Credentials().token)
