import discord
from discord.ext import commands
from datetime import datetime, timezone
import asyncio

from core import checks
from core.models import PermissionLevel

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

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user}!')

    @commands.command()
    @is_allowed_role()
    async def training(self, ctx):
        # Step 2: Ask for time selection
        time_options = [
            "12 AM EST / 5 AM BST",
            "5 AM EST / 10 AM BST",
            "10 AM EST / 3 PM BST",
            "3 PM EST / 8 PM BST",
            "8 PM EST / 1 AM BST"
        ]

        # Create a dropdown menu for time selection
        select = discord.ui.Select(placeholder="Select a time...", options=[discord.SelectOption(label=time) for time in time_options])

        async def select_callback(interaction):
            selected_time = select.values[0]
            await interaction.response.defer()

            # Step 3: Confirm time selection
            confirm_embed = discord.Embed(
                title="Confirm Training Time",
                description=f"Would you like to post the training message for **{selected_time}**?",
                color=0x00FF00
            )
            confirm_view = discord.ui.View()
            confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.success)
            cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)

            async def confirm_callback(interaction):
                await self.send_training_message(ctx, selected_time)
                await interaction.response.send_message("Training message sent!", ephemeral=True)

            async def cancel_callback(interaction):
                await interaction.response.send_message("Training command cancelled.", ephemeral=True)

            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback

            confirm_view.add_item(confirm_button)
            confirm_view.add_item(cancel_button)

            await ctx.send(embed=confirm_embed, view=confirm_view)

        select.callback = select_callback

        view = discord.ui.View()
        view.add_item(select)
        await ctx.send("Select a training time:", view=view)

    async def send_training_message(self, ctx, selected_time):
        training_channel_id = self.training_channel_ids.get(ctx.guild.id, ctx.channel.id)
        role_id = self.training_mention_roles.get(ctx.guild.id, 695243187043696650)
        session_ping = f"<@&{role_id}>"
        host_mention = ctx.author.mention
        start_time_unix = int(datetime.now(timezone.utc).timestamp())

        embed = discord.Embed(
            title="Training Session",
            description=f"A training session is scheduled at **{selected_time}**. Join us!",
            color=0x00FF00
        )
        embed.add_field(name="Host", value=host_mention, inline=False)
        embed.add_field(name="Session Status", value=f"Scheduled <t:{start_time_unix}:R>", inline=False)

        channel = self.bot.get_channel(training_channel_id)
        if channel:
            start_button = discord.ui.Button(label="Start Training", style=discord.ButtonStyle.primary)
            lock_button = discord.ui.Button(label="Lock Training", style=discord.ButtonStyle.secondary)
            end_button = discord.ui.Button(label="End Training", style=discord.ButtonStyle.danger, disabled=True)

            view = discord.ui.View(timeout=10800)  # 3 hours timeout
            view.add_item(start_button)
            view.add_item(lock_button)
            view.add_item(end_button)

            msg = await channel.send(f"{session_ping}", embed=embed, view=view)

            # Button callbacks
            async def start_callback(interaction: discord.Interaction):
                start_button.disabled = True
                end_button.disabled = False
                lock_button.disabled = False

                embed.description += "\n**Training has started!**"
                await msg.edit(embed=embed, view=view)

            async def lock_callback(interaction: discord.Interaction):
                lock_button.disabled = True
                embed.description += "\n**Session Status:** Locked"
                await msg.edit(embed=embed, view=view)

            async def end_callback(interaction: discord.Interaction):
                embed.title = "Training Ended"
                embed.description += "\nThe training session has ended. Thank you for participating!"
                await msg.edit(embed=embed, view=None)

            start_button.callback = start_callback
            lock_button.callback = lock_callback
            end_button.callback = end_callback

            await ctx.send("Training session scheduled!")
        else:
            await ctx.send("The specified channel could not be found.")

    @commands.command()
    @is_admin_user()
    async def trainingmention(self, ctx, role: discord.Role):
        self.training_mention_roles[ctx.guild.id] = role.id
        await ctx.send(f"Training mention role set to {role.mention}.")

    @commands.command()
    @is_admin_user()
    async def trainingchannel(self, ctx, channel: discord.TextChannel):
        self.training_channel_ids[ctx.guild.id] = channel.id
        await ctx.send(f"Training messages will now be sent in {channel.mention}.")

    @commands.command()
    @is_admin_user()
    async def trainingconfig(self, ctx):
        # Restrict command usage to specific channel
        if ctx.channel.id != 836283712193953882:
            await ctx.send("Wrong channel buddy")
            return

        config_info = f"""```yaml
    Training Start Times: {self.training_start_times}
    Training Channel IDs: {self.training_channel_ids}
    Training Mention Roles: {self.training_mention_roles}
    Allowed Roles: {ALLOWED_ROLES}
    Admin Users: {ADMIN_USERS}
    ```"""
    
        await ctx.send(config_info)

# Async function to set up the cog
async def setup(bot):
    await bot.add_cog(TrainingManager(bot))
