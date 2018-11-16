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
    # if message.content.startswith("~move "):  # `~move <name> set <x> <y>` Absolute
    #     args = shlex.split(message.content[6:])  # `~move <name> <x> <y>`     Relative
    #     name = args[0]  # Name is the first arg
    #     combatant = objects.get_combatant(name)  # Get combatant name `name`
    #     if args[1] == 'set':  # If Set, then use absolute
    #         abso = True
    #         x = args[2]
    #         y = int(args[3])
    #     else:  # Else Relative
    #         abso = False
    #         x = args[1]
    #         y = int(args[2])
    #     if combatant:  # If combatant found
    #         Move = move(build, combatant, x, y, abso)  # Move combatant
    #         await bot.change_presence(game=discord.Game(name="Updating..."))
    #         build = GetPresentation(PRESENTATION_ID)  # Update Build
    #         objects = ObjectList(build)  # Update Object List
    #         await bot.send_message(message.channel, Move.message)  # Send move message
    #         await bot.change_presence(game=discord.Game(name="Making a bot"))
    #     else:  # Else Return Error
    #         await bot.send_message(message.channel,
    #                                   "Error: No combatant found named '{}'".format(name))
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
    build = functions.GetPresentation(PRESENTATION_ID)  # Update Build
    objects = functions.ObjectList(build)  # Update Object List
    await bot.change_presence(game=discord.Game(name="Making a bot"))
    await bot.add_reaction(ctx.message, '\u2705')

#
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
