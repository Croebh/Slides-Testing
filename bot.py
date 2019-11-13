import shlex
import discord
import re
from discord.ext import commands
from discord.errors import Forbidden, HTTPException, NotFound
from discord.ext.commands.errors import CommandInvokeError
import functions


# If modifying these scopes, delete the file token.json.
SCOPES = 'https://www.googleapis.com/auth/presentations'

# The ID of a sample presentation.
PRESENTATION_ID = '1iPbghn_hquZlwZDpKzOttonCl5tyF8809q8NJJOgT0w'


build = functions.GetPresentation(PRESENTATION_ID)
objects = functions.ObjectList(build)

bot = commands.Bot(command_prefix='~')


@bot.event
async def on_message(message):
    global build
    global objects
    if message.author == bot.user:
        return
    if message.content == "Hello":
        await message.channel.send("World")
    await bot.process_commands(message)


@bot.command()
async def exit(ctx):
    if ctx.message.author.id == Credentials().owner:
        await ctx.add_reaction('\u2705')
        await bot.logout()
    else:
        await ctx.send("Error: You are not authorized to use this command")


@bot.command(name='pos', aliases=['position', 'p'])
async def pos(ctx, name: str):
    print(name)
    print('Getting coords for - '+name)
    combatant = objects.get_combatant(name)
    if combatant:
        await ctx.send("{0.name} is at ({0.pos})".format(combatant))
    else:
        await ctx.send('Error: No combatant found named {}'.format(name))


@bot.command(aliases=['comp', 'distance'])
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
        await ctx.message.channel.send(embed=embed)
    elif combatant1 and combatant2:
        distance = functions.Distance(combatant1, combatant2)
        embed = discord.Embed(title="{0.name} is at ({0.pos})".format(combatant1))
        embed.add_field(name="{0.name} is at ({0.pos})".format(combatant2),
                        value="{0.ft} ft. away, {0.compass} ({0.degree}°)".format(distance))
        await ctx.send(embed=embed)


@bot.command()
async def range(ctx, x, y:int, maxrange:int=None):
    if str(x).isalpha():
        x = x.upper()
        embed = discord.Embed(title="Distances from ({}, {})".format(x, y))
        x = functions.alpha_conv(x.upper())
    else:
        embed = discord.Embed(title="Distances from ({}, {})".format(functions.alpha_conv(int(x)), y))
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
    await ctx.send(embed=embed)

@bot.command()
async def get(ctx, name: str):
    combatant = objects.get_combatant(name)
    if combatant:
        await ctx.send('{0.name} is a creature of {0.size} size, at coordinates ({0.pos}), and whose id is {0.objectId}'.format(
                                   combatant))
    else:
        await ctx.message.channel.send("Error: No combatant found named '{}'".format(name))


@bot.command()
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
        async with ctx.typing():
            Move = functions.Move(build, combatant, x, y, abso)  # Move combatant
            if Move.moving:
                await bot.change_presence(activity=discord.Game(name="Updating..."))
                build = functions.GetPresentation(PRESENTATION_ID)  # Update Build
                objects = functions.ObjectList(build)  # Update Object List
                await bot.change_presence(activity=discord.Game(name="Making a bot"))
        embed = discord.Embed(title="Moving {}".format(combatant.name))
        embed.add_field(name=Move.title, value=Move.message)
        await ctx.send(embed=embed)  # Send move message
    else:  # Else Return Error
        await ctx.send("Error: No combatant found named '{}'".format(name))


@bot.command()
async def size(ctx):
    await ctx.send("Size of the slide is {} Squares.".format(build.size))


@bot.command(aliases=['update'])
async def refresh(ctx):
    global build
    global objects
    await bot.change_presence(activity=discord.Game(name="Updating..."))
    async with ctx.typing():
        build = functions.GetPresentation(PRESENTATION_ID)  # Update Build
        objects = functions.ObjectList(build)  # Update Object List
    await ctx.send('Updated!')
    await bot.change_presence(activity=discord.Game(name="Making a bot"))

# Full Credit to github.com/zhu.exe for this, modified from the one used on github.com/avrae/avrae
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return

    elif isinstance(error, (commands.UserInputError, commands.NoPrivateMessage, ValueError)):
        return await ctx.send(
            f"Error: {str(error)}\nUse `{ctx.prefix}help " + ctx.command.qualified_name + "` for help.")

    elif isinstance(error, commands.CheckFailure):
        msg = str(error) or "You are not allowed to run this command."
        return await ctx.send(f"Error: {msg}")

    elif isinstance(error, commands.CommandOnCooldown):
        return await ctx.send("This command is on cooldown for {:.1f} seconds.".format(error.retry_after))

    elif isinstance(error, CommandInvokeError):
        original = error.original

        if isinstance(original, Forbidden):
            try:
                return await ctx.author.send(
                    f"Error: I am missing permissions to run this command. "
                    f"Please make sure I have permission to send messages to <#{ctx.channel.id}>."
                )
            except HTTPException:
                try:
                    return await ctx.send(f"Error: I cannot send messages to this user.")
                except HTTPException:
                    return

        elif isinstance(original, NotFound):
            return await ctx.send("Error: I tried to edit or delete a message that no longer exists.")

        elif isinstance(original, HTTPException):
            if original.response.status == 400:
                return await ctx.send(f"Error: Message is too long, malformed, or empty.\n{original.text}")
            elif original.response.status == 500:
                return await ctx.send("Error: Internal server error on Discord's end. Please try again.")

        elif isinstance(original, OverflowError):
            return await ctx.send(f"Error: A number is too large for me to store.")

    await ctx.send(f"Error: {str(error)}\nUh oh, that wasn't supposed to happen! ")


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    await bot.change_presence(activity=discord.Game(name="Making a bot"))


class Credentials:
    def __init__(self):
        try:
            import credentials
        except ImportError:
            raise Exception("Credentials not found.")
        self.token = credentials.token
        self.owner = credentials.owner


bot.run(Credentials().token)
