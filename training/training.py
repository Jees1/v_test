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
                color=0x00ff00  # Change to your desired color
            )
            embed.add_field(name="Host", value=f"{host_mention} | {ctx.author}{' | ' + ctx.author.nick if ctx.author.nick else ''}", inline=False)
            embed.add_field(name="Session Status", value="Waiting for the host to begin the training", inline=False)
            embed.add_field(name="Scheduled Time", value=selected_time, inline=False)
            embed.add_field(name="Training Center Link", value="[Click here](https://www.roblox.com/games/4780049434/Vinns-Training-Center)", inline=False)
            embed.set_footer(text=f"Started by: {interaction.user.name}")

            channel = self.bot.get_channel(training_channel_id)
            if channel:
                start_button = discord.ui.Button(label="Start Training", style=discord.ButtonStyle.success)
                view = discord.ui.View()
                view.add_item(start_button)

                async def start_training_callback(interaction):
                    await self.start_training_callback(interaction, msg.id)
                
                start_button.callback = start_training_callback
                
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
        if not channel:
            await interaction.response.send_message("The training channel could not be found.", ephemeral=True)
            return

        try:
            msg = await channel.fetch_message(message_id)
            if msg.embeds and msg.author.id == self.bot.user.id:
                embed = msg.embeds[0]
                if embed.title == "Training":
                    embed.set_field_at(1, name="Session Status", value="Training has started!", inline=False)
                    await msg.edit(embed=embed)

                    update_button = discord.ui.Button(label="Update Status", style=discord.ButtonStyle.secondary)
                    view = discord.ui.View()
                    view.add_item(update_button)

                    update_button.callback = lambda interaction: self.update_status_callback(interaction, msg.id)
                    await msg.edit(view=view)
                    await interaction.response.send_message(f"{emoji} | Training has started!", ephemeral=True)
                else:
                    await interaction.response.send_message("The message provided isn't valid.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    async def update_status_callback(self, interaction, message_id):
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
            msg = await channel.fetch_message(message_id)
            if msg.embeds and msg.author.id == self.bot.user.id:
                embed = msg.embeds[0]
                options = ["End Training", "Lock Training"]
                action_select = discord.ui.Select(placeholder="Choose an action...", options=options)
    
                async def action_callback(interaction):
                    selected_action = action_select.values[0]
                    if selected_action == "End Training":
                        await self.end_training_callback(interaction, msg.id)
                    elif selected_action == "Lock Training":
                        lock_time_unix = int(datetime.now(timezone.utc).timestamp())
                        new_embed = discord.Embed(
                            title="Training Locked",
                            description=f"The training session is now locked. Time locked: <t:{lock_time_unix}>",
                            color=0xED4245
                        )
                        new_embed.set_footer(text=embed.footer.text)

                        try:
                            await msg.edit(embed=new_embed)
                            await interaction.response.send_message(f"{emoji} | Training has been locked.", ephemeral=True)
                        except Exception as e:
                            await self.send_error_log(f"Error editing embed during Lock Training: {str(e)}", ctx, "Error Editing Embed")
                            await interaction.response.send_message("An error occurred while trying to update the training status.", ephemeral=True)
    
                action_select.callback = action_callback
                view = discord.ui.View()
                view.add_item(action_select)
                await interaction.response.send_message("Select an action:", view=view, ephemeral=True)
            else:
                await interaction.response.send_message("The message provided does not contain an embed or isn't valid.", ephemeral=True)
        except discord.NotFound:
            await interaction.response.send_message("Message not found.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to access the message.", ephemeral=True)
        except Exception as e:
            await self.send_error_log(f"Unexpected error: {str(e)}", ctx, "Unexpected Error")
            await interaction.response.send_message("An unexpected error occurred.", ephemeral=True)

    async def end_training_callback(self, interaction, message_id):
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
            msg = await channel.fetch_message(message_id)
            if msg.embeds and msg.author.id == self.bot.user.id:
                delete_time_unix = int(datetime.now(timezone.utc).timestamp() + 600)  # 10 minutes
                embed = msg.embeds[0]

                if embed.title == "Training":
                    host_field = embed.fields[0].value
                    embed.title = "Training Ended"
                    embed.description = f"The training hosted by {host_field} has just ended. Thank you for attending! Deleting this message <t:{delete_time_unix}:R>"
                    embed.color = 0xED4245
                    await msg.edit(embed=embed)
                    await interaction.response.send_message("Training has ended!", ephemeral=True)

                    await asyncio.sleep(600)  # Wait 10 minutes before deleting
                    await msg.delete()
                else:
                    await interaction.response.send_message("The message provided isn't valid.", ephemeral=True)
        except Exception as e:
            await self.send_error_log(f"Unexpected error: {str(e)}", ctx, "Unexpected Error")
            await interaction.response.send_message("An unexpected error occurred.", ephemeral=True)

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
