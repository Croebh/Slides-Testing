import shlex
import discord
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
        await bot.say("{0.name} is at ({0.coords[0]}, {0.coords[1]})".format(combatant))
    else:
        await bot.say('Error: No combatant found named {}'.format(name))


@bot.command(pass_context=True, aliases=['comp', 'distance'])
async def compass(ctx, name1, name2=None):
    combatant1 = objects.get_combatant(name1)
    combatant2 = objects.get_combatant(name2)
    if combatant1 and not combatant2:
        out = []
        out.append("{0.name} is at {0.coords}".format(combatant1))
        for other in objects.list:
            if other['objectId'] != combatant1.objectId:
                combatant2 = objects.get_combatant(other['name'])
                distance = functions.Distance(combatant1, combatant2)
                out.append("{0.name} is {1.ft} ft {1.compass} ({1.degree}°) at {0.coords}".format(
                    combatant2, distance
                ))
        await bot.say('\n'.join(out))
    elif combatant1 and combatant2:
        distance = functions.Distance(combatant1, combatant2)
        await bot.say("{0.name} is {2.ft} feet from {1.name}, on the heading {2.compass} ({2.degree}°) at {1.coords}".format(
            combatant1, combatant2, distance
        ))


@bot.command()
async def get(name: str):
    combatant = objects.get_combatant(name)
    if combatant:
        await bot.say('{0.name} is a creature of {0.size} size, at coordinates {0.coords}, and whose id is {0.objectId}'.format(
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
        await bot.change_presence(game=discord.Game(name="Updating..."))
        build = functions.GetPresentation(PRESENTATION_ID)  # Update Build
        objects = functions.ObjectList(build)  # Update Object List
        await bot.say(Move.message)  # Send move message
        await bot.change_presence(game=discord.Game(name="Making a bot"))
    else:  # Else Return Error
        await bot.say("Error: No combatant found named '{}'".format(name))


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
