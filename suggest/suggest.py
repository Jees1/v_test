import discord
from discord.ext import commands
from discord.ui import View, Select
from core import checks
from core.models import PermissionLevel
import asyncio

class Suggest(commands.Cog):
    """
    Lets you send a suggestion to a designated channel using a menu.
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
        The user types their suggestion, then chooses the appropriate channel.
        """
        try:
            if ctx.guild.id == 686214712354144387:
                # Define the channels
                discChannel = self.bot.get_channel(686858225743822883)
                trainingChannel = self.bot.get_channel(686253519350923280)
                hotelChannel = self.bot.get_channel(777656824098062385)

                # Create the embed for the suggestion
                suggestEmbed = discord.Embed(description=suggestion, color=self.bot.main_color)
                suggestEmbed.set_footer(text="Vinns Hotel Suggestions | -suggest")
                suggestEmbed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)

                # Create the select menu for the user to choose a channel
                class ChannelSelect(View):
                    def __init__(self, ctx, suggestion, *args, **kwargs):
                        super().__init__(*args, **kwargs)
                        self.ctx = ctx
                        self.suggestion = suggestion

                    @discord.ui.select(
                        placeholder="Choose a channel to send your suggestion",
                        options=[
                            discord.SelectOption(label="Discord Suggestion", description="Send to the Discord suggestion channel", value="discord"),
                            discord.SelectOption(label="Hotel Suggestion", description="Send to the hotel suggestion channel", value="hotel"),
                            discord.SelectOption(label="Training Center Suggestion", description="Send to the training center channel", value="training"),
                        ]
                    )
                    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
                        if interaction.user != self.ctx.author:
                            await interaction.response.send_message("You cannot interact with this menu.", ephemeral=True)
                            return

                        # Choose the channel based on the user's selection
                        selected_channel = None
                        if select.values[0] == "discord":
                            selected_channel = discChannel
                        elif select.values[0] == "hotel":
                            selected_channel = hotelChannel
                        elif select.values[0] == "training":
                            selected_channel = trainingChannel

                        if selected_channel:
                            # Send the suggestion to the selected channel
                            sugmsg = await selected_channel.send(content=f"<@!{self.ctx.author.id}>", embed=self.suggestion)
                            await interaction.response.send_message(f"✅ Successfully sent your suggestion to <#{selected_channel.id}>", ephemeral=True)

                            # Add reaction options to the suggestion message for approval, neutral, disapproval
                            for emoji in (
                                '<:Approve:818120227387998258>', 
                                '<:Neutral:818120929057046548>', 
                                '<:Disapprove:818120194135425024>'
                            ):
                                await sugmsg.add_reaction(emoji)
                            self.stop()  # Stop the menu interaction once the user selects a channel.

                # Send a message prompting the user and attach the menu
                view = ChannelSelect(ctx, suggestEmbed)
                await ctx.send(content=f"<@!{ctx.author.id}>, please choose the channel to send your suggestion to:", embed=suggestEmbed, view=view)

        except discord.ext.commands.CommandOnCooldown:
            await ctx.send("❌ You are on cooldown. Please try again later.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Suggest(bot))
