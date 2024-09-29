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

emoji = "<:cow:1012643349150314496>"

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

    async def send_error_log(self, error, ctx, error_type):
        target_guild_id = 835809403424604190
        target_channel_id = 836283712193953882
    
        target_guild = self.bot.get_guild(target_guild_id)
        if target_guild:
            target_channel = target_guild.get_channel(target_channel_id)
            if target_channel:
                await target_channel.send(f"**Error:** {error}\n**Error Type:** `{error_type}`\n**Context:** {ctx}")
            else:
                print("Target channel not found.")
        else:
            print("Target guild not found.")

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
            description="A shift is currently being hosted at the hotel! Come to the hotel for a nice and comfy room! Active staff may get a chance of promotion.",
            color=self.bot.main_color
        )
        embed.add_field(name="Host", value=f"{host_mention} | {ctx.author}{' | ' + ctx.author.nick if ctx.author.nick else ''}", inline=False)
        embed.add_field(name="Session Status", value=f"Started <t:{start_time_unix}:R>", inline=False)
        embed.add_field(name="Hotel Link", value="[Click here](https://www.roblox.com/games/4766198689/Work-at-a-Hotel-Vinns-Hotels)", inline=False)
        embed.set_footer(text="Vinns Sessions")

        channel = self.bot.get_channel(shift_channel_id)
        if channel:
            msg = await channel.send(f"{session_ping}", embed=embed)

            self.shift_start_times[ctx.guild.id] = (datetime.now(timezone.utc), msg.id)

            await ctx.send(f"{emoji} | Shift has been started!")
        else:
            await ctx.send("The specified channel could not be found.")

    async def end_shift(self, msg, host_mention):
        delete_time_unix = int(datetime.now(timezone.utc).timestamp() + 600)  # 10 minutes
        embed = msg.embeds[0]

        embed.title = "Shift Ended"
        embed.description = f"The shift hosted by {host_mention} has just ended. Thank you for attending! We appreciate your presence and look forward to seeing you at future shifts.\n\nDeleting this message <t:{delete_time_unix}:R>"
        embed.color = 0xED4245
        embed.clear_fields()
        await msg.edit(embed=embed)

        # Wait for 10 minutes before deleting the message
        await asyncio.sleep(600)
        await msg.delete()

    @commands.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    @is_admin_user()
    async def shiftmention(self, ctx, role: discord.Role):
        self.shift_mention_roles[ctx.guild.id] = role.id
        await ctx.send(f"{emoji} | Shift mention role set to {role.mention}.")

    @commands.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    @is_admin_user()
    async def shiftchannel(self, ctx, channel: discord.TextChannel):
        self.shift_channel_ids[ctx.guild.id] = channel.id
        await ctx.send(f"{emoji} | Shift messages will now be sent in {channel.mention}.")

    @commands.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    @is_admin_user()
    async def shiftconfig(self, ctx):
        if ctx.channel.id != 836283712193953882:
            await ctx.send("Wrong channel buddy")
            return
    
        config_info = f"""```yaml
    Shift Start Times: {self.shift_start_times}
    Shift Channel IDs: {self.shift_channel_ids}
    Shift Mention Roles: {self.shift_mention_roles}
    Allowed Roles: {ALLOWED_ROLES}
    Admin Users: {ADMIN_USERS}
    ```"""
    
        await ctx.send(config_info)

    @shift.error
    async def shift_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("You need to specify a role to mention. Usage: `-shift`.")
        elif isinstance(error, commands.MissingRole):
            await ctx.send("You don't have the required role to use this command.")
        else:
            await self.send_error_log(error, ctx, "shift_error")
            print(f"Error: {error}")

    @shiftmention.error
    @shiftchannel.error
    async def command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use this command.")
        else:
            await self.send_error_log(error, ctx, "command_error")
            print(f"Error: {error}")

async def setup(bot):
    await bot.add_cog(ShiftManager(bot))
