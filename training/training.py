import discord
from discord.ext import commands
from datetime import datetime, timezone

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
            await interaction.response.defer()
            selected_time = time_select.values[0]
            self.training_start_times[ctx.guild.id] = (selected_time, datetime.now(timezone.utc))

            training_channel_id = ctx.channel.id  # Use current channel for simplicity
            role_id = 738396997135892540  # Default role ID
            session_ping = f"<@&{role_id}>"
            host_mention = ctx.author.mention

            embed = discord.Embed(
                title="Training",
                description="Training is being hosted! Join for a possible promotion.",
                color=0x00ff00
            )
            embed.add_field(name="Host", value=host_mention, inline=False)
            embed.add_field(name="Session Status", value="Waiting to start", inline=False)
            embed.add_field(name="Scheduled Time", value=selected_time, inline=False)

            channel = self.bot.get_channel(training_channel_id)
            if channel:
                view = discord.ui.View()

                start_button = discord.ui.Button(label="Start Training", style=discord.ButtonStyle.success)
                view.add_item(start_button)

                async def start_training_callback(interaction):
                    await self.start_training_callback(interaction, ctx.guild.id)

                start_button.callback = start_training_callback

                end_button = discord.ui.Button(label="End Training", style=discord.ButtonStyle.danger)
                view.add_item(end_button)

                async def end_training_callback(interaction):
                    await self.end_training_callback(interaction, ctx.guild.id)

                end_button.callback = end_training_callback

                msg = await channel.send(f"{session_ping}", embed=embed, view=view)
                self.training_start_times[ctx.guild.id] = (selected_time, msg.id)
                await ctx.send(f"{emoji} | Training has been initialized!")
            else:
                await ctx.send("The specified channel could not be found.")

        time_select.callback = time_callback
        await ctx.send("Please select the training time:", view=discord.ui.View().add_item(time_select))

    async def start_training_callback(self, interaction, guild_id):
        await interaction.response.send_message("Training has started!", ephemeral=True)

    async def end_training_callback(self, interaction, guild_id):
        await interaction.response.defer()  # Acknowledge the interaction
        if guild_id not in self.training_start_times:
            await interaction.followup.send("No active training found for this server.", ephemeral=True)
            return
        
        training_channel_id = self.training_channel_ids.get(guild_id, None)
        if training_channel_id is None:
            await interaction.followup.send("No training channel set.", ephemeral=True)
            return

        channel = self.bot.get_channel(training_channel_id)
        if not channel:
            await interaction.followup.send("The training channel could not be found.", ephemeral=True)
            return

        try:
            msg = await channel.fetch_message(self.training_start_times[guild_id][1])
            embed = msg.embeds[0]
            embed.title = "Training Ended"
            embed.description = "The training has just ended. Thank you for attending!"
            await msg.edit(embed=embed)
            await interaction.followup.send("Training has ended!", ephemeral=True)
        except Exception as e:
            await self.send_error_log(f"Error ending training: {str(e)}", interaction, "End Training Error")
            await interaction.followup.send("An error occurred while ending the training.", ephemeral=True)

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

async def setup(bot):
    await bot.add_cog(TrainingManager(bot))
