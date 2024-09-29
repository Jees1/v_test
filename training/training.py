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

            training_channel_id = self.training_channel_ids.get(ctx.guild.id, ctx.channel.id)
            role_id = self.training_mention_roles.get(ctx.guild.id, 738396997135892540)
            session_ping = f"<@&{role_id}>"
            host_mention = ctx.author.mention

            embed = discord.Embed(
                title="Training",
                description="Training is being hosted at the Training Center! Join for a possible promotion.",
                color=0x00ff00
            )
            embed.add_field(name="Host", value=f"{host_mention} | {ctx.author}{' | ' + ctx.author.nick if ctx.author.nick else ''}", inline=False)
            embed.add_field(name="Session Status", value="Waiting for the host to begin the training", inline=False)
            embed.add_field(name="Scheduled Time", value=selected_time, inline=False)
            embed.add_field(name="Training Center Link", value="[Click here](https://www.roblox.com/games/4780049434/Vinns-Training-Center)", inline=False)
            embed.set_footer(text=f"Started by: {interaction.user.name}")

            channel = self.bot.get_channel(training_channel_id)
            if channel:
                view = discord.ui.View()

                # Start Training button
                start_button = discord.ui.Button(label="Start Training", style=discord.ButtonStyle.success)
                view.add_item(start_button)

                async def start_training_callback(interaction):
                    await self.start_training_callback(interaction, msg.id)

                start_button.callback = start_training_callback

                # Lock Training button (initially disabled)
                lock_button = discord.ui.Button(label="Lock Training", style=discord.ButtonStyle.secondary, disabled=True)
                async def lock_training_callback(interaction):
                    await self.lock_training_callback(interaction)

                lock_button.callback = lock_training_callback
                view.add_item(lock_button)

                # End Training button (initially disabled)
                end_button = discord.ui.Button(label="End Training", style=discord.ButtonStyle.danger, disabled=True)
                async def end_training_callback(interaction):
                    await self.end_training_callback(interaction, msg.id)

                end_button.callback = end_training_callback
                view.add_item(end_button)

                try:
                    msg = await channel.send(f"{session_ping}", embed=embed, view=view)
                    self.training_start_times[ctx.guild.id] = (selected_time, msg.id)
                    await ctx.send(f"{emoji} | Training has been initialized! Please select a time.")
                except Exception as e:
                    await self.send_error_log(e, ctx, "Error sending training message")
            else:
                await ctx.send("The specified channel could not be found.")

        time_select.callback = time_callback
        await ctx.send("Please select the training time:", view=discord.ui.View().add_item(time_select))
    
    async def start_training_callback(self, interaction, message_id):
        ctx = await self.bot.get_context(interaction.message)
    
        if ctx.guild.id not in self.training_start_times:
            await interaction.response.send_message("No active training found for this server.", ephemeral=True)
            return
    
        training_channel_id = self.training_channel_ids.get(ctx.guild.id, ctx.channel.id)
        channel = self.bot.get_channel(training_channel_id)
    
        try:
            msg = await channel.fetch_message(message_id)
            if msg.embeds and msg.author.id == self.bot.user.id:
                embed = msg.embeds[0]
                embed.set_field_at(1, name="Session Status", value="Training has started!", inline=False)
    
                # Create buttons
                start_button = discord.ui.Button(label="Start Training", style=discord.ButtonStyle.success, disabled=True)
                lock_button = discord.ui.Button(label="Lock Training", style=discord.ButtonStyle.secondary)
                end_button = discord.ui.Button(label="End Training", style=discord.ButtonStyle.danger)
    
                # Assign the callbacks directly
                lock_button.callback = self.lock_training_callback
                end_button.callback = lambda interaction: self.end_training_callback(interaction, msg.id)  # Correct callback assignment
    
                # Create a new view and add buttons
                action_buttons = discord.ui.View()
                action_buttons.add_item(start_button)
                action_buttons.add_item(lock_button)
                action_buttons.add_item(end_button)
    
                await interaction.response.defer()  # Acknowledge the interaction
                await msg.edit(embed=embed, view=action_buttons)
                await interaction.followup.send("Training has started!", ephemeral=True)
            else:
                await interaction.response.send_message("The message provided isn't valid.", ephemeral=True)
        except Exception as e:
            await self.send_error_log(f"Error in start_training_callback: {str(e)}", ctx, "Start Training Error")
            await interaction.response.send_message("An error occurred. Please try again.", ephemeral=True)

    async def lock_training_callback(self, interaction):
        ctx = await self.bot.get_context(interaction.message)
    
        if ctx.guild.id not in self.training_start_times:
            await interaction.response.send_message("No active training found for this server.", ephemeral=True)
            return
    
        training_channel_id = self.training_channel_ids.get(ctx.guild.id, ctx.channel.id)
        channel = self.bot.get_channel(training_channel_id)
        if not channel:
            await interaction.response.send_message("The training channel could not be found.", ephemeral=True)
            return
    
        try:
            msg = await channel.fetch_message(self.training_start_times[ctx.guild.id][1])
            if msg.embeds and msg.author.id == self.bot.user.id:
                embed = msg.embeds[0]
                if embed.title == "Training":
                    lock_time_unix = int(datetime.now(timezone.utc).timestamp())
                    embed.title = "Training Locked"
                    embed.description = f"The training session is now locked. Time locked: <t:{lock_time_unix}>"
                    embed.set_field_at(1, name="Session Status", value="Training Locked", inline=False)
                    embed.color = 0xED4245
    
                    # Create a new view and set button states
                    new_view = discord.ui.View()
                    start_button = discord.ui.Button(label="Start Training", style=discord.ButtonStyle.success, disabled=True)
                    lock_button = discord.ui.Button(label="Lock Training", style=discord.ButtonStyle.secondary, disabled=True)
                    end_button = discord.ui.Button(label="End Training", style=discord.ButtonStyle.danger, disabled=False)  # Enable End Training button
    
                    # Add buttons to the view
                    new_view.add_item(start_button)
                    new_view.add_item(lock_button)
                    new_view.add_item(end_button)
    
                    await msg.edit(embed=embed, view=new_view)
                    await interaction.response.send_message(f"{emoji} | Training has been locked.", ephemeral=True)
                else:
                    await interaction.response.send_message("The message provided isn't valid.", ephemeral=True)
        except Exception as e:
            await self.send_error_log(f"Unexpected error: {str(e)}", ctx, "Unexpected Error")
            await interaction.response.send_message("An unexpected error occurred.", ephemeral=True)

    async def end_training_callback(self, interaction, message_id):
        print("End Training Callback Triggered")  # Debug message
        ctx = await self.bot.get_context(interaction.message)

        await self.send_error_log("Starting end_training_callback", ctx, "Debug")

        # Check if there is active training
        if ctx.guild.id not in self.training_start_times:
            await self.send_error_log("No active training found", ctx, "Debug")
            await interaction.response.send_message("No active training found for this server.", ephemeral=True)
            return

        training_channel_id = self.training_channel_ids.get(ctx.guild.id, ctx.channel.id)
        channel = self.bot.get_channel(training_channel_id)

        if not channel:
            await self.send_error_log("Training channel not found", ctx, "Debug")
            await interaction.response.send_message("The training channel could not be found.", ephemeral=True)
            return

        try:
            await interaction.response.defer()  # Acknowledge the interaction
            await self.send_error_log("Fetching message", ctx, "Debug")

            msg = await channel.fetch_message(message_id)

            if msg.embeds and msg.author.id == self.bot.user.id:
                embed = msg.embeds[0]
                host_field = embed.fields[0].value

                embed.title = "Training Ended"
                embed.description = f"The training hosted by {host_field} has just ended. Thank you for attending!"
                embed.color = 0xED4245

                # Create a new view and disable all buttons
                new_view = discord.ui.View()
                new_view.add_item(discord.ui.Button(label="Start Training", disabled=True))
                new_view.add_item(discord.ui.Button(label="Lock Training", disabled=True))
                new_view.add_item(discord.ui.Button(label="End Training", disabled=True))

                await msg.edit(embed=embed, view=new_view)
                await interaction.followup.send("Training has ended!", ephemeral=True)
                await self.send_error_log("Training ended successfully", ctx, "Debug")
            else:
                await interaction.followup.send("The message provided isn't valid.", ephemeral=True)
                await self.send_error_log("Invalid message", ctx, "Debug")
        except Exception as e:
            await self.send_error_log(f"Unexpected error: {str(e)}", ctx, "End Training Error")
            await interaction.followup.send("An unexpected error occurred. Please try again later.", ephemeral=True)

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
