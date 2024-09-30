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
        self.locked_training_sessions = {}

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

        time_select = discord.ui.Select(
            placeholder="Select the training time...",
            options=[discord.SelectOption(label=time) for time in time_options]
        )

        async def time_callback(interaction):
            ctx.send(f"Selected Time: {time_select.values[0]}")
            await interaction.response.defer()
            selected_time = time_select.values[0]
            self.training_start_times[ctx.guild.id] = (selected_time, datetime.now(timezone.utc))

            training_channel_id = ctx.channel.id
            self.training_channel_ids[ctx.guild.id] = training_channel_id

            role_id = self.training_mention_roles.get(ctx.guild.id, 738396997135892540)
            session_ping = f"<@&{role_id}>"
            host_mention = ctx.author.mention

            embed = discord.Embed(
                title="Training",
                description="Training is being hosted! Join for a possible promotion.",
                color=0x00ff00
            )
            embed.add_field(name="Host", value=host_mention, inline=False)
            embed.add_field(name="Session Status", value="Waiting for the host to begin the training", inline=False)
            embed.add_field(name="Scheduled Time", value=selected_time, inline=False)
            embed.add_field(name="Training Center Link", value="[Click here](https://www.roblox.com/games/4780049434/Vinns-Training-Center)", inline=False)

            channel = self.bot.get_channel(training_channel_id)
            if channel:
                view = discord.ui.View()

                start_button = discord.ui.Button(label="Start Training", style=discord.ButtonStyle.success, persistent=True)
                view.add_item(start_button)

                async def start_training_callback(interaction):
                    await self.start_training_callback(interaction, ctx.guild.id)

                start_button.callback = start_training_callback

                lock_button = discord.ui.Button(label="Lock Training", style=discord.ButtonStyle.secondary, disabled=True, persistent=True)
                view.add_item(lock_button)

                async def lock_training_callback(interaction):
                    await self.lock_training_callback(interaction, ctx.guild.id)

                lock_button.callback = lock_training_callback

                end_button = discord.ui.Button(label="End Training", style=discord.ButtonStyle.danger, disabled=True, persistent=True)
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
        view = discord.ui.View()
        view.add_item(time_select)

        await ctx.send("Please select the training time:", view=view)

    async def start_training_callback(self, interaction, guild_id):
        await interaction.response.defer()
    
        if guild_id not in self.training_start_times:
            await interaction.followup.send("No active training found for this server.", ephemeral=True)
            return
    
        training_channel_id = self.training_channel_ids.get(guild_id)
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
            embed.set_field_at(1, name="Session Status", value="Training in progress", inline=False)
    
            # Update button states after training starts
            view = discord.ui.View()
            #start_button = discord.ui.Button(label="Start Training", style=discord.ButtonStyle.success, disabled=True)
            lock_button = discord.ui.Button(label="Lock Training", style=discord.ButtonStyle.secondary, persistent=True)
            end_button = discord.ui.Button(label="End Training", style=discord.ButtonStyle.danger, persistent=True)
            #view.add_item(start_button)
            view.add_item(lock_button)
            view.add_item(end_button)
    
            await msg.edit(embed=embed, view=view)
            await interaction.followup.send("Training has started!", ephemeral=True)
        except Exception as e:
            await self.send_error_log(f"Error starting training: {str(e)}", interaction, "Start Training Error")
            await interaction.followup.send("An error occurred while starting the training.", ephemeral=True)


    async def lock_training_callback(self, interaction, guild_id):
        try:
            # Acknowledge the interaction to avoid timeout
            await interaction.response.defer()
    
            # Check if there is an active training session
            if guild_id not in self.training_start_times:
                await interaction.followup.send("No active training found for this server.", ephemeral=True)
                return
    
            training_channel_id = self.training_channel_ids.get(guild_id)
            if training_channel_id is None:
                await interaction.followup.send("No training channel set.", ephemeral=True)
                return
    
            channel = self.bot.get_channel(training_channel_id)
            if not channel:
                await interaction.followup.send("The training channel could not be found.", ephemeral=True)
                return
    
            # Fetch the message to be edited
            try:
                msg_id = self.training_start_times[guild_id][1]
                msg = await channel.fetch_message(msg_id)
            except discord.NotFound:
                await interaction.followup.send("Training message not found.", ephemeral=True)
                return
    
            # Modify the embed and view
            embed = msg.embeds[0]
            embed.set_field_at(1, name="Session Status", value="Training session locked", inline=False)
            embed.color = 0xED4245
    
            # Disable the buttons
            view = discord.ui.View()
            start_button = discord.ui.Button(label="Start Training", style=discord.ButtonStyle.success, disabled=True, persistent=True)
            lock_button = discord.ui.Button(label="Lock Training", style=discord.ButtonStyle.secondary, disabled=True, persistent=True)
            end_button = discord.ui.Button(label="End Training", style=discord.ButtonStyle.danger, persistent=True)
            view.add_item(start_button)
            view.add_item(lock_button)
            view.add_item(end_button)
    
            # Edit the message with the new embed and view
            await msg.edit(embed=embed, view=view)
            await interaction.followup.send("Training has been locked.", ephemeral=True)
    
        except Exception as e:
            await self.send_error_log(f"Error locking training: {str(e)}", interaction, "Lock Training Error")
            await interaction.followup.send("An error occurred while locking the training.", ephemeral=True)
    



    async def end_training_callback(self, interaction, guild_id):
        try:
            await interaction.response.defer()
    
            # Check if there is an active training session
            if guild_id not in self.training_start_times:
                await interaction.followup.send("No active training found for this server.", ephemeral=True)
                return
    
            training_channel_id = self.training_channel_ids.get(guild_id)
            if training_channel_id is None:
                await interaction.followup.send("No training channel set.", ephemeral=True)
                return
    
            channel = self.bot.get_channel(training_channel_id)
            if not channel:
                await interaction.followup.send("The training channel could not be found.", ephemeral=True)
                return
    
            # Fetch the message to be edited
            try:
                msg_id = self.training_start_times[guild_id][1]
                msg = await channel.fetch_message(msg_id)
            except discord.NotFound:
                await interaction.followup.send("Training message not found.", ephemeral=True)
                return
    
            # Modify the embed and view
            embed = msg.embeds[0]
            embed.set_field_at(1, name="Session Status", value="Training session ended", inline=False)
            embed.color = 0xED4245
    
            # Disable all buttons
            view = discord.ui.View()
            start_button = discord.ui.Button(label="Start Training", style=discord.ButtonStyle.success, disabled=True, persistent=True)
            lock_button = discord.ui.Button(label="Lock Training", style=discord.ButtonStyle.secondary, disabled=True, persistent=True)
            end_button = discord.ui.Button(label="End Training", style=discord.ButtonStyle.danger, disabled=True, persistent=True)
            view.add_item(start_button)
            view.add_item(lock_button)
            view.add_item(end_button)
    
            # Edit the message with the new embed and view
            await msg.edit(embed=embed, view=view)
            await interaction.followup.send("Training has ended.", ephemeral=True)
    
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
