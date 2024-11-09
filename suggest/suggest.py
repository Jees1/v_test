import discord
from discord.ext import commands
from core import checks
from core.models import PermissionLevel
import asyncio

class Suggest(commands.Cog):
    """
    Lets you send a suggestion to a designated channel.
    """

    def __init__(self, bot):
        self.bot = bot
        self.coll = bot.plugin_db.get_partition(self)

    @commands.command()
    @checks.has_permissions(PermissionLevel.REGULAR)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def suggest(self, ctx, *, suggestion):
        """
        Suggest something!

        **Usage**:
        -suggest You should add cars so guests can be driven to their rooms.
        """
        try:
            if ctx.guild.id == 686214712354144387:
                discChannel = self.bot.get_channel(686858225743822883)
                trainingChannel = self.bot.get_channel(686253519350923280)
                hotelChannel = self.bot.get_channel(777656824098062385)

                # Create a select menu with the different suggestion categories
                options = [
                    discord.SelectOption(label="Discord Suggestion", emoji="<:Discord:795240449103233024>", value="discord"),
                    discord.SelectOption(label="Hotel Suggestion", emoji="🏨", value="hotel"),
                    discord.SelectOption(label="Training Center Suggestion", emoji="<:studio:639558945584840743>", value="training"),
                    discord.SelectOption(label="Cancel Command", emoji="❌", value="cancel")
                ]
                
                select = discord.ui.Select(placeholder="Choose the type of your suggestion...", options=options)

                # View to handle the select menu
                class SuggestionView(discord.ui.View):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, **kwargs)

                    # Callback for when a user selects an option
                    @discord.ui.select(placeholder="Choose the type of your suggestion...", options=options)
                    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
                        # Ensure that the user who triggered the command is the one interacting with the select menu
                        if interaction.user != ctx.author:
                            await interaction.response.send_message("You are not authorized to use this menu.", ephemeral=True)
                            return
                        
                        selected_value = select.values[0]  # Get the first selected value
                        
                        # Create the suggestion embed
                        suggestEmbed = discord.Embed(description=suggestion, color=self.bot.main_color)
                        suggestEmbed.set_footer(text="Vinns Hotel Suggestions | -suggest")
                        suggestEmbed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)

                        # Send the suggestion to the appropriate channel based on the selection
                        if selected_value == "discord":
                            await discChannel.send(content=f"<@!{interaction.user.id}>", embed=suggestEmbed)
                            await interaction.response.edit_message(content=f"✅ | Successfully sent your suggestion to <#{discChannel.id}>", embed=None)
                        elif selected_value == "hotel":
                            await hotelChannel.send(content=f"<@!{interaction.user.id}>", embed=suggestEmbed)
                            await interaction.response.edit_message(content=f"✅ | Successfully sent your suggestion to <#{hotelChannel.id}>", embed=None)
                        elif selected_value == "training":
                            await trainingChannel.send(content=f"<@!{interaction.user.id}>", embed=suggestEmbed)
                            await interaction.response.edit_message(content=f"✅ | Successfully sent your suggestion to <#{trainingChannel.id}>", embed=None)
                        elif selected_value == "cancel":
                            await interaction.response.edit_message(content="❌ | Command cancelled.", embed=None)

                        # Disable the select menu after interaction
                        select.disabled = True
                        await interaction.message.edit(view=self)

                # Create a view and add the select menu to it
                view = SuggestionView(timeout=60)  # Set timeout to 60 seconds
                await ctx.send("Please select the type of your suggestion:", view=view)

        except discord.ext.commands.CommandOnCooldown:
            print("Cooldown triggered.")

# Async function to set up the cog
async def setup(bot):
    await bot.add_cog(Suggest(bot))
