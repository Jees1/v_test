import discord
from discord.ext import commands
from discord.ui import View, Select, Modal, TextInput
from core import checks
from core.models import PermissionLevel
import asyncio

class Suggest(commands.Cog):
    """
    Lets you send a suggestion to a designated channel using an interactive sequence.
    """

    def __init__(self, bot):
        self.bot = bot
        self.coll = bot.plugin_db.get_partition(self)

    @commands.command()
    @checks.has_permissions(PermissionLevel.REGULAR)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def suggest(self, ctx):
        """
        Starts the suggestion process where the user inputs their suggestion and selects a channel.
        """
        try:
            # Step 1: Ask for the suggestion text
            modal = Modal(title="Suggestion", custom_id="suggestion_modal")
            modal.add_item(TextInput(label="Please type your suggestion:", placeholder="Type your suggestion here..."))
            
            # Wait for the modal response
            await ctx.send_modal(modal)

            # Wait for the modal response asynchronously
            interaction = await self.bot.wait_for('modal_submit', check=lambda inter: inter.user == ctx.author)

            suggestion = interaction.data['components'][0]['value']  # The text the user entered
            await interaction.response.send_message("Got your suggestion! Now, let's choose the channel.")

            # Step 2: Ask for the channel selection using a dropdown menu
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

                    # Define the channels
                    discChannel = self.bot.get_channel(686858225743822883)
                    hotelChannel = self.bot.get_channel(777656824098062385)
                    trainingChannel = self.bot.get_channel(686253519350923280)

                    # Select the appropriate channel
                    selected_channel = None
                    if select.values[0] == "discord":
                        selected_channel = discChannel
                    elif select.values[0] == "hotel":
                        selected_channel = hotelChannel
                    elif select.values[0] == "training":
                        selected_channel = trainingChannel

                    if selected_channel:
                        # Send the suggestion to the selected channel
                        suggest_embed = discord.Embed(description=suggestion, color=self.bot.main_color)
                        suggest_embed.set_footer(text="Vinns Hotel Suggestions | -suggest")
                        suggest_embed.set_author(name=self.ctx.author, icon_url=self.ctx.author.avatar.url)

                        sugmsg = await selected_channel.send(content=f"<@!{self.ctx.author.id}>", embed=suggest_embed)
                        
                        await interaction.response.send_message(f"✅ Successfully sent your suggestion to <#{selected_channel.id}>", ephemeral=True)
                        
                        # Add reaction options to the suggestion message for approval, neutral, disapproval
                        for emoji in (
                            '<:Approve:818120227387998258>', 
                            '<:Neutral:818120929057046548>', 
                            '<:Disapprove:818120194135425024>'
                        ):
                            await sugmsg.add_reaction(emoji)

                        self.stop()  # Stop the menu interaction once the user selects a channel.

            # Send the dropdown menu for channel selection
            view = ChannelSelect(ctx, suggestion)
            await ctx.send(content="Now, please select the channel to send your suggestion to:", view=view)

        except discord.ext.commands.CommandOnCooldown:
            await ctx.send("❌ You are on cooldown. Please try again later.")
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")

async def setup(bot):
    await bot.add_cog(Suggest(bot))
