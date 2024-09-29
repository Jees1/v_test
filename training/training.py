import discord
from discord.ext import commands
from datetime import datetime, timezone
import asyncio

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

    async def send_error_log(self, error, ctx, error_type):
        target_channel = self.bot.get_channel(836283712193953882)
        if target_channel:
            await target_channel.send(f"**Error:** {error}\n**Error Type:** `{error_type}`\n**Context:** {ctx}")

    def is_allowed_role():
        async def predicate(ctx):
            return any(role.id in ALLOWED_ROLES for role in ctx.author.roles)
        return commands.check(predicate)

    def is_admin_user():
        async def predicate(ctx):
            return ctx.author.id in ADMIN_USERS
        return commands.check(predicate)

    @commands.command(aliases=['train'])
    @is_allowed_role()
    async def training(self, ctx):
        time_options = [
            "12 AM EST / 5 AM BST",
            "5 AM EST / 10 AM BST",
            "10 AM EST / 3 PM BST",
            "3 PM EST / 8 PM BST",
            "8 PM EST / 1 AM BST"
        ]

        time_select = discord.ui.Select(placeholder="Select the training time...", options=[discord.SelectOption(label=time) for time in time_options])

        async def time_callback(interaction):
            await interaction.response.defer()  # Acknowledge the interaction
            selected_time = time_select.values[0]
            self.training_start_times[ctx.guild.id] = (selected_time, datetime.now(timezone.utc))

            training_channel_id = self.training_channel_ids.get(ctx.guild.id, ctx.channel.id)
            role_id = self.training_mention_roles.get(ctx.guild.id, 738396997135892540)
            session_ping = f"<@&{role_id}>"
            host_mention = ctx.author.mention

            embed = discord.Embed(
                title="Training",
                description="Training is being hosted at the Training Center! Join for a possible promotion.",
                color=0x00ff00
            )
            embed.add_field(name="Host", value=host_mention, inline=False)
            embed.add_field(name="Session Status", value="Waiting for the host to begin the training", inline=False)
            embed.add_field(name="Scheduled Time", value=selected_time, inline=False)

            channel = self.bot.get_channel(training_channel_id)
            if channel:
                start_button = discord.ui.Button(label="Start Training", style=discord.ButtonStyle.success)
                view = discord.ui.View()
                view.add_item(start_button)

                async def start_training_callback(interaction):
                    await self.start_training_callback(interaction, ctx)

                start_button.callback = start_training_callback
                await channel.send(f"{session_ping}", embed=embed, view=view)
                await ctx.send("Training has been initialized!")
            else:
                await ctx.send("The specified channel could not be found.")

        time_select.callback = time_callback
        await ctx.send("Please select the training time:", view=discord.ui.View().add_item(time_select))

    async def start_training_callback(self, interaction, ctx):
        await interaction.response.defer()
        self.training_start_times[ctx.guild.id] = (ctx, datetime.now(timezone.utc))

        embed = discord.Embed(
            title="Training",
            description="The training has started!",
            color=0x00ff00
        )
        update_button = discord.ui.Button(label="Update Status", style=discord.ButtonStyle.secondary)
        update_view = discord.ui.View()
        update_view.add_item(update_button)

        async def update_status_callback(interaction):
            await self.update_status_callback(interaction, ctx)

        update_button.callback = update_status_callback

        channel = self.training_channel_ids.get(ctx.guild.id, ctx.channel.id)
        message = await channel.send(embed=embed, view=update_view)
        self.training_start_times[ctx.guild.id] = (message.id, datetime.now(timezone.utc))

    async def update_status_callback(self, interaction, ctx):
        await interaction.response.defer()

        channel = self.training_channel_ids.get(ctx.guild.id, ctx.channel.id)
        if not channel:
            await interaction.followup.send("Training channel not found.", ephemeral=True)
            return

        try:
            message_id = self.training_start_times[ctx.guild.id][0]
            message = await channel.fetch_message(message_id)

            embed = message.embeds[0]
            embed.add_field(name="New Status", value="Updated Status Here", inline=False)  # Customize your status update
            await message.edit(embed=embed)
            await interaction.followup.send("Status updated!", ephemeral=True)
        except Exception as e:
            await self.send_error_log(str(e), ctx, "Update Status Error")
            await interaction.followup.send("Failed to update status.", ephemeral=True)

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
        if ctx.channel.id != 836283712193953882:  # Ensure the command is used in the correct channel
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

async def setup(bot):
    await bot.add_cog(TrainingManager(bot))
