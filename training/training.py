import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone
import asyncio

from core import checks
from core.models import PermissionLevel

ALLOWED_ROLES = [
    796317014209462332,
    686258158049558772,
    686257925815402660,
    769203966004953118,
    686219247206137900
]

MODIFY_ALLOWED = [
    796317014209462332,
    686257925815402660,
    769203966004953118,
    686219247206137900
]

ADMIN_USERS = [
    497582356064894997,
    349899849937846273
]

emoji = "<:cow:1012643349150314496>"

channel_id = 741830399956877312
ping_role_id = 695243187043696650

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

    @commands.command(aliases=["train"])
    @is_allowed_role()
    @checks.has_permissions(PermissionLevel.REGULAR)
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def training(self, ctx):
        time_options = [
            "4 AM EST / 9 AM GMT",
            "9 AM EST / 2 PM GMT",
            "2 PM EST / 7 PM GMT",
            "7 PM EST / 12 AM GMT",
            "11 PM EST / 4 AM GMT"
        ]

        select = discord.ui.Select(placeholder="Select a time...", options=[discord.SelectOption(label=time) for time in time_options])

        async def select_callback(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message(f"{emoji} | You are not authorized to use this menu.", ephemeral=True)
                return
            
            select.disabled = True
            selected_time = select.values[0]
            await interaction.response.defer()  # Acknowledge the interaction
            await interaction.message.edit(view=view)
            
            confirm_embed = discord.Embed(
                title="Confirm Training Time",
                description=f"Would you like to post the training message for **{selected_time}**?",
                color=0x57F287
            )
            confirm_view = discord.ui.View(timeout=60)  # Timeout after 60 seconds
            confirm_button = discord.ui.Button(label="Confirm", style=discord.ButtonStyle.success)
            cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.danger)

            async def confirm_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not authorized to confirm this action.", ephemeral=True)
                    return
                await interaction.response.send_message(f"{emoji} | Training message will be sent!", ephemeral=True)
                await self.send_training_message(ctx, selected_time)
                confirm_button.disabled = True
                cancel_button.disabled = True
                await interaction.message.edit(view=confirm_view)  # Update message to disable buttons
                # confirm_view.stop()  # Stop the view

            async def cancel_callback(interaction):
                if interaction.user != ctx.author:
                    await interaction.response.send_message("You are not authorized to cancel this action.", ephemeral=True)
                    return
                await interaction.response.send_message("Training command cancelled.", ephemeral=True)
                confirm_button.disabled = True
                cancel_button.disabled = True
                await interaction.message.edit(view=confirm_view)  # Update message to disable buttons
                # confirm_view.stop()  # Stop the view

            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback

            confirm_view.add_item(confirm_button)
            confirm_view.add_item(cancel_button)

            confirm_view.on_timeout = lambda: [setattr(confirm_button, 'disabled', True), setattr(cancel_button, 'disabled', True)]

            await interaction.followup.send(embed=confirm_embed, view=confirm_view)

        select.callback = select_callback

        view = discord.ui.View()
        view.add_item(select)
        await ctx.send("Select a training time:", view=view)

    async def send_training_message(self, ctx, selected_time):
        #training_channel_id = self.training_channel_ids.get(ctx.guild.id, channel_id)
        #role_id = self.training_mention_roles.get(ctx.guild.id, ping_role_id)
        session_ping = f"<@&{ping_role_id}>"
        host_mention = ctx.author.mention

        

        embed = discord.Embed(
            title="Training Session",
            description=f"A training is being hosted at **{selected_time}**! Join the Training Center for a possible promotion. Trainees up to Junior Staff may attend to get promotion, while Senior Staff and above may assist.",
            color=0x57F287
        )
        embed.add_field(name="Host", value=host_mention, inline=False)
        embed.add_field(name="Scheduled Time", value=selected_time, inline=False)
        embed.add_field(name="Session Status", value=f"Waiting for the host to start the training...", inline=False)
        embed.set_footer(text=f"Scheduled by: {ctx.author.name}")

        channel = self.bot.get_channel(channel_id)
        if channel:
            start_button = discord.ui.Button(label="Start Training", style=discord.ButtonStyle.success)
            lock_button = discord.ui.Button(label="Lock Training", style=discord.ButtonStyle.secondary, disabled=True)
            end_button = discord.ui.Button(label="End Training", style=discord.ButtonStyle.danger, disabled=True)

            view = discord.ui.View(timeout=108000)  # 3 hours timeout
            view.add_item(start_button)
            view.add_item(lock_button)
            view.add_item(end_button)

            msg = await channel.send(f"{session_ping}", embed=embed, view=view)

            async def start_callback(interaction: discord.Interaction):
                if not any(role.id in MODIFY_ALLOWED for role in interaction.user.roles) and interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("You do not have permission to start the training.", ephemeral=True)
                    return

                start_time_unix = int(datetime.now(timezone.utc).timestamp())
                embed.set_field_at(2, name="Session Status", value=f"Started <t:{start_time_unix}:R>")  # Update session status
                start_button.disabled = True
                end_button.disabled = False
                lock_button.disabled = False
                embed.color = self.bot.main_color
                embed.set_footer(text=f"Started by: {ctx.author.name} | {embed.footer.text}")
                await msg.edit(embed=embed, view=view)
                await interaction.response.defer()  # Acknowledge the interaction

            async def lock_callback(interaction: discord.Interaction):
                if not any(role.id in MODIFY_ALLOWED for role in interaction.user.roles) and interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("You do not have permission to lock the training.", ephemeral=True)
                    return

                lock_time_unix = int(datetime.now(timezone.utc).timestamp())
                embed.set_footer(text=f"Locked by: {ctx.author.name} | {embed.footer.text}")
                embed.title = "🔒 | Training Locked"
                embed.color = 0xFFA500
                embed.set_field_at(2, name="Session Status", value=f"Locked <t:{lock_time_unix}:R>")  # Update session status
                lock_button.disabled = True
                await msg.edit(embed=embed, view=view)
                await interaction.response.defer()  # Acknowledge the interaction

            async def end_callback(interaction: discord.Interaction):
                if not any(role.id in MODIFY_ALLOWED for role in interaction.user.roles) and interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("You do not have permission to end the training.", ephemeral=True)
                    return
            
                try:
                    await self.end_training(msg, embed, ctx.author.name, automatic=False)
                    await interaction.response.defer()  # Acknowledge the interaction
                except discord.NotFound:
                    print("The interaction was not found. It may have expired.")

                
            start_button.callback = start_callback
            lock_button.callback = lock_callback
            end_button.callback = end_callback

            view.on_timeout = lambda: asyncio.create_task(self.end_training(msg, embed, "The training session has timed out due to inactivity.", automatic=True))
            await ctx.send("Training session scheduled!")
        else:
            await ctx.send("The specified channel could not be found.")

    
    async def end_training(self, msg, embed, name, automatic=False):
        delete_time_unix = int(datetime.now(timezone.utc).timestamp()) + 600  # 600 = 10 mins
        embed.title = "Training Ended"
        if automatic:
            embed.set_footer(text=f"Ended automatically | {embed.footer.text}")
        else:
            embed.set_footer(text=f"Ended by: {name} | {embed.footer.text}")
        
        embed.description = f"The training session hosted by {name} has just ended. We appreciate your presence and look forward to seeing you at future trainings\n\nDeleting this message <t:{delete_time_unix}:R>"
        embed.clear_fields()
        embed.color = 0xF04747
        await msg.edit(embed=embed, view=None)
        await asyncio.sleep(600)
        await msg.delete()

    @commands.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    @is_admin_user()
    async def trainingmention(self, ctx, role: discord.Role):
        self.training_mention_roles[ctx.guild.id] = role.id
        await ctx.send(f"Training mention role set to {role.mention}.")

    @commands.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    @is_admin_user()
    async def trainingchannel(self, ctx, channel: discord.TextChannel):
        self.training_channel_ids[ctx.guild.id] = channel.id
        await ctx.send(f"Training messages will now be sent in {channel.mention}.")

    @commands.command()
    @checks.has_permissions(PermissionLevel.OWNER)
    @is_admin_user()
    async def trainingconfig(self, ctx):
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

    @training.error
    async def training_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"{ctx.author.mention} please wait {int(error.retry_after)} seconds before using this command again.")

# Async function to set up the cog
async def setup(bot):
    await bot.add_cog(TrainingManager(bot))
