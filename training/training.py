
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

class TrainingManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.training_start_times = {}
        self.training_channel_ids = {}
        self.training_mention_roles = {}

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

    @commands.command(aliases=['train'])
    @checks.has_permissions(PermissionLevel.REGULAR)
    @is_allowed_role()
    async def training(self, ctx):
        self.training_start_times[ctx.guild.id] = datetime.now(timezone.utc)
        training_channel_id = self.training_channel_ids.get(ctx.guild.id, ctx.channel.id)
        role_id = self.training_mention_roles.get(ctx.guild.id, 695243187043696650)
        session_ping = f"<@&{role_id}>"
        host_mention = ctx.author.mention
        start_time_unix = int(self.training_start_times[ctx.guild.id].timestamp())

        embed = discord.Embed(
            title="Training",
            description=f"A training is currently being hosted at the training center!",
            color=self.bot.main_color
        )
        embed.add_field(name="Host", value=f"{host_mention} | {ctx.author}{' | ' + ctx.author.nick if ctx.author.nick else ''}", inline=False)
        embed.add_field(name="Session Status", value=f"Started <t:{start_time_unix}:R>", inline=False)
        embed.add_field(name="Training Link", value="[Click here](https://www.roblox.com/games/4780049434/Vinns-Training-Center)", inline=False)
        embed.set_footer(text=f"Vinns Sessions")

        channel = self.bot.get_channel(training_channel_id)
        if channel:
            msg = await channel.send(f"{session_ping}", embed=embed)
            self.training_start_times[ctx.guild.id] = (datetime.now(timezone.utc), msg.id)
            await ctx.send(f"{emoji} | Training has been started!\n\n`msgID: {msg.id}`")
        else:
            await ctx.send("The specified channel could not be found.")

    @commands.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    @is_admin_user()
    async def trainingmention(self, ctx, role: discord.Role):
        self.training_mention_roles[ctx.guild.id] = role.id
        await ctx.send(f"{emoji} | Training mention role set to {role.mention}.")

    @commands.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    @is_admin_user()
    async def trainingchannel(self, ctx, channel: discord.TextChannel):
        self.training_channel_ids[ctx.guild.id] = channel.id
        await ctx.send(f"{emoji} | Training messages will now be sent in {channel.mention}.")

    @commands.command(aliases=['et'])
    @checks.has_permissions(PermissionLevel.REGULAR)
    @is_allowed_role()
    async def endtraining(self, ctx, message_id: int):
        if ctx.guild.id not in self.training_start_times:
            await ctx.send("No active training found for this server.")
            return
    
        training_channel_id = self.training_channel_ids.get(ctx.guild.id, ctx.channel.id)
        channel = self.bot.get_channel(training_channel_id)
        if not channel:
            await ctx.send("The training channel could not be found.")
            return
    
        try:
            msg = await channel.fetch_message(message_id)
            if msg.embeds and msg.author.id == 738395338393518222:
                delete_time_unix = int(datetime.now(timezone.utc).timestamp() + 600) # 600 seconds = 10 minutes
                embed = msg.embeds[0]
                if embed.title == "Training":
                    host_field = embed.fields[0].value
                    embed.title = "Training Ended"
                    embed.description = f"The training hosted by {host_field} has just ended. Thank you for attending! We appreciate your presence and look forward to seeing you at future trainings.\n\nDeleting this message <t:{delete_time_unix}:R>"
                    embed.color = 0xED4245
                    embed.clear_fields()
                    await msg.edit(embed=embed)
                    await ctx.send(f"{emoji} | Training with message ID `{message_id}` has ended.")
        
                    # Wait for 15 minutes before deleting the message
                    await asyncio.sleep(600)  # 600 seconds = 10 minutes
                    await msg.delete()  # Delete the edited message after 10 minutes
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
    @checks.has_permissions(PermissionLevel.OWNER)
    @is_admin_user()
    async def trainingconfig(self, ctx):
        # Restrict command usage to specific channel
        if ctx.channel.id != 836283712193953882:
            await ctx.send("Wrong channel buddy")
            return
    
        # Create a string representation of the current configuration
        config_info = f"""```yaml
    Training Start Times: {self.training_start_times}
    Training Channel IDs: {self.training_channel_ids}
    Training Mention Roles: {self.training_mention_roles}
    Allowed Roles: {ALLOWED_ROLES}
    Admin Users: {ADMIN_USERS}
    ```"""
    
        await ctx.send(config_info)
    

@endtraining.error
async def endtraining_error(self, ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please provide the message ID for the training to end. Usage: `-endtraining <msgID>`.") 
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid message ID provided.")
    else:
        await ctx.send("An unexpected error occurred.")
        print(f"Unexpected error in endtraining command: {error}")
        await self.send_error_log(error, ctx, "endtraining_error")

@training.error
async def training_error(self, ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("You need to specify a role to mention. Usage: `-training`.")
    elif isinstance(error, commands.MissingRole):
        await ctx.send("You don't have the required role to use this command.")
    else:
        await ctx.send("An unexpected error occurred.")
        print(f"Unexpected error in training command: {error}")
        await self.send_error_log(error, ctx, "training_error")

@trainingmention.error
@trainingchannel.error
async def command_error(self, ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have permission to use this command.")
    else:
        await ctx.send("An unexpected error occurred.")
        print(f"Unexpected error in command: {error}")
        await self.send_error_log(error, ctx, "command_error")


#bot = commands.Bot(command_prefix='-', intents=discord.Intents.all())
async def setup(bot):
    await bot.add_cog(TrainingManager(bot))
