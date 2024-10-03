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
    686219247206137900
]

ADMIN_USERS = [
    497582356064894997,
    349899849937846273
]

emoji = "<:cow:1012643349150314496>"

channel_id = 780879678730666086
ping_role_id = 695243187043696650

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
        shift_channel_id = self.shift_channel_ids.get(ctx.guild.id, ping_role_id)
        role_id = self.shift_mention_roles.get(ctx.guild.id, role_id)
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
        embed.set_footer(text=f"Vinns Sessions")

        channel = self.bot.get_channel(shift_channel_id)
        if channel:
            # Create a button for ending the shift manually
            button = discord.ui.Button(label="End Shift", style=discord.ButtonStyle.danger)

            # Create a view with a timeout of 3 hours (10800 seconds)
            view = discord.ui.View(timeout=10800)  
            view.add_item(button)

            # Send the shift announcement
            msg = await channel.send(f"{session_ping}", embed=embed, view=view)
            self.shift_start_times[ctx.guild.id] = (datetime.now(timezone.utc), msg.id)

            # Button callback for manually ending the shift
            async def button_callback(interaction: discord.Interaction):
                await interaction.response.defer()
                # Check if the user has an allowed role
                if any(role.id in ALLOWED_ROLES for role in interaction.user.roles):
                    await self.end_shift(ctx, msg, interaction.user)
                    await interaction.response.send_message("Shift has ended.", ephemeral=True)
                else:
                    await interaction.response.send_message("You do not have permission to end the shift.", ephemeral=True)


            button.callback = button_callback

            # Handle the timeout (automatic shift end)
            async def view_timeout():
                await self.end_shift(ctx, msg, None)

            view.on_timeout = view_timeout

            await ctx.send(f"Shift has been started!")

        else:
            await ctx.send("The specified channel could not be found.")

    
    async def end_shift(self, ctx, msg, ended_by_user):
        shift_channel_id = self.shift_channel_ids.get(ctx.guild.id, ctx.channel.id)
        channel = self.bot.get_channel(shift_channel_id)
        if not channel:
            print("The shift channel could not be found.")
            return

        try:
            # Fetch the message we want to edit
            original_msg = await channel.fetch_message(msg.id)
            if original_msg.embeds and original_msg.author.id == self.bot.user.id:
                embed = original_msg.embeds[0]
                
                # Update the embed to indicate the shift has ended
                if embed.title == "Shift":
                    host_field = embed.fields[0].value
                    delete_time_unix = int(datetime.now(timezone.utc).timestamp() + 600)  # 10 minutes until message deletion

                    embed.title = "Shift Ended"
                    embed.description = f"The shift hosted by {host_field} has just ended. Thank you for attending! We appreciate your presence and look forward to seeing you at future shifts.\n\nDeleting this message <t:{delete_time_unix}:R>"
                    embed.color = 0xED4245
                    if ended_by_user:
                        embed.set_footer(text=f"Ended by: {ended_by_user.name}")
                    else:
                        embed.set_footer(text="Ended automatically after timeout.")
                    embed.clear_fields()

                    # Edit the message with the updated embed
                    await original_msg.edit(embed=embed, view=None)

                    # Wait 10 minutes before deleting the message
                    await asyncio.sleep(600)  # 600 seconds = 10 minutes
                    await original_msg.delete()
                else:
                    print("The message provided isn't valid.")
        except discord.NotFound:
            print("Message not found.")
        except discord.Forbidden:
            print("I don't have permission to access the message.")
        except discord.HTTPException as e:
            print(f"An error occurred while trying to fetch or edit the message: {e}")

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
        # Restrict command usage to specific channel
        if ctx.channel.id != 836283712193953882:
            await ctx.send("Wrong channel buddy")
            return
    
        # Create a string representation of the current configuration
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

#bot = commands.Bot(command_prefix='-', intents=discord.Intents.all())
async def setup(bot):
    await bot.add_cog(ShiftManager(bot))
