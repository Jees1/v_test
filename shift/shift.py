
import discord
from discord.ext import commands
from datetime import datetime, timezone
import asyncio

from core import checks
from core.models import DummyMessage, PermissionLevel

ALLOWED_ROLES = [
    796317014209462332,
    686258158049558772,
    686257925815402660,
    769203966004953118,
    707474741124005928,
    1283839837589344306,
    695243187043696650
]

ADMIN_USERS = [
    497582356064894997,
    349899849937846273
]

class ShiftManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.shift_start_times = {}
        self.shift_channel_ids = {}
        self.shift_mention_roles = {}

    def is_allowed_role():
        async def predicate(ctx):
            return any(role.id in ALLOWED_ROLES for role in ctx.author.roles)
        return commands.check(predicate)

    def is_admin_user():
        async def predicate(ctx):
            return ctx.author.id in ADMIN_USERS
        return commands.check(predicate)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user}!')

    @commands.command(aliases=['s'])
    @checks.has_permissions(PermissionLevel.REGULAR)
    @is_allowed_role()
    async def shift(self, ctx):
        self.shift_start_times[ctx.guild.id] = datetime.now(timezone.utc)
        shift_channel_id = self.shift_channel_ids.get(ctx.guild.id, ctx.channel.id)
        role_id = self.shift_mention_roles.get(ctx.guild.id, 695243187043696650)
        session_ping = f"<@&{role_id}>"
        host_mention = ctx.author.mention
        start_time_unix = int(self.shift_start_times[ctx.guild.id].timestamp())

        embed = discord.Embed(
            title="Shift",
            description=f"A shift is currently being hosted at the hotel! Come to the hotel for a nice and comfy room! Active staff may get a chance of promotion.",
            color=self.bot.main_color
        )
        embed.add_field(name="Host", value=f"{host_mention} | {ctx.author}{' | ' + ctx.author.nick if ctx.author.nick else ''}", inline=False)
        embed.add_field(name="Session Status", value=f"Started <t:{start_time_unix}:R>", inline=False)
        embed.add_field(name="Hotel Link", value="[Click here](https://www.roblox.com/games/4766198689/Work-at-a-Hotel-Vinns-Hotels)", inline=False)
        embed.set_footer(text=f"Vinns Hotel")

        channel = self.bot.get_channel(shift_channel_id)
        if channel:
            msg = await channel.send(f"{session_ping}", embed=embed)
            self.shift_start_times[ctx.guild.id] = (datetime.now(timezone.utc), msg.id)
            await ctx.send(f"<:cow:1012643349150314496> | Shift has been started!\n`msgID: {msg.id}`")
        else:
            await ctx.send("The specified channel could not be found.")

    @commands.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    @is_admin_user()
    async def shiftmention(self, ctx, role: discord.Role):
        self.shift_mention_roles[ctx.guild.id] = role.id
        await ctx.send(f"<:cow:1012643349150314496> | Shift mention role set to {role.mention}.")

    @commands.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    @is_admin_user()
    async def shiftchannel(self, ctx, channel: discord.TextChannel):
        self.shift_channel_ids[ctx.guild.id] = channel.id
        await ctx.send(f"<:cow:1012643349150314496> | Shift messages will now be sent in {channel.mention}.")

    @commands.command(aliases=['es'])
    @checks.has_permissions(PermissionLevel.REGULAR)
    @is_allowed_role()
    async def endshift(self, ctx, message_id: int):
        if ctx.guild.id not in self.shift_start_times:
            await ctx.send("No active shift found for this server.")
            return
    
        shift_channel_id = self.shift_channel_ids.get(ctx.guild.id, ctx.channel.id)
        channel = self.bot.get_channel(shift_channel_id)
        if not channel:
            await ctx.send("The shift channel could not be found.")
            return
    
        try:
            msg = await channel.fetch_message(message_id)
            if msg.embeds and msg.author.id == 738395338393518222:
                delete_time_unix = int(datetime.now(timezone.utc).timestamp() + 600) # 600 seconds = 10 minutes
                embed = msg.embeds[0]
                if embed.title == "Shift":
                    host_field = embed.fields[0].value
                    embed.title = "Shift Ended"
                    embed.description = f"The shift hosted by {host_field} has just ended. Thank you for attending! We appreciate your presence and look forward to seeing you at future shifts.\n\nDeleting this message <t:{delete_time_unix}:R>"
                    embed.color = 0xED4245
                    embed.clear_fields()
                    await msg.edit(embed=embed)
                    await ctx.send(f"<:cow:1012643349150314496> | Shift with message ID `{message_id}` has ended.")
        
                    # Wait for 15 minutes before deleting the message
                    await asyncio.sleep(600)  # 600 seconds = 10 minutes
                    await msg.delete()  # Delete the edited message after 15 minutes
                else:
                    await ctx.send("The message provided isn't valid.")
            else:
                await ctx.send("The message provided does not contain an embed or isn't valid.")
        except discord.NotFound:
            await ctx.send("Message not found.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to access the message.")
        except discord.HTTPException as e:
            await ctx.send("An error occurred while trying to fetch or edit the message.")

    @commands.command()
    async def eval(self, ctx, *, code: str):
        """Evaluate Python code."""
        if ctx.author.id != 349899849937846273:
            return

        code = code.strip('`')  # Strip out any surrounding backticks
        env = {
            'discord': discord,
            'commands': commands,
            'ctx': ctx,
            'bot': self.bot,
            'channel': ctx.channel,
            'guild': ctx.guild,
            'author': ctx.author,
            '__import__': __import__,
        }

        stdout = io.StringIO()
        try:
            with io.StringIO() as buf, redirect_stdout(buf):
                exec(code, env)
                output = buf.getvalue()
        except Exception as e:
            output = str(e)
            traceback_str = traceback.format_exc()

        if output:
            await ctx.send(f'Output:\n```\n{output}\n```')
        if traceback_str:
            await ctx.send(f'Traceback:\n```\n{traceback_str}\n```')

    @eval.error
    async def eval_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide the code to evaluate.")
        else:
            await ctx.send("An unexpected error occurred.")
            print(f"Eval Error: {error}")


    @shift.error
    async def shift_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You need to specify a role to mention. Usage: `-shift`.")
        elif isinstance(error, commands.MissingRole):
            await ctx.send("You don't have the required role to use this command.")
        else:
            await ctx.send("An unexpected error occurred.")
            print(f"Error: {error}")

    @shiftmention.error
    @shiftchannel.error
    async def command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use this command.")
        else:
            await ctx.send("An unexpected error occurred.")
            print(f"Error: {error}")

    @endshift.error
    async def endshift_error(self, ctx, error):
        
        target_guild_id = 835809403424604190
        target_channel_id = 836283712193953882
        
        
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please provide the message ID for the shift to end. Usage: `-endshift <msgID>`.")
        else:
            await ctx.send("An unexpected error occurred.")
            
            # Get the target channel in the other guild
            target_guild = self.bot.get_guild(target_guild_id)
            if target_guild:
                target_channel = target_guild.get_channel(target_channel_id)
                if target_channel:
                    # Send the error details to the specified channel
                    await target_channel.send(f"EndShift Error: {error}\nError Type: {type(error)}\nContext: {ctx}")
                else:
                    print("Target channel not found.")
            else:
                print("Target guild not found.")


#bot = commands.Bot(command_prefix='-', intents=discord.Intents.all())
async def setup(bot):
    await bot.add_cog(ShiftManager(bot))
