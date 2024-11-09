import discord
from discord.ext import commands
from discord.ui import Select, View
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

                # Create a dropdown (select menu) with the suggestion categories
                options = [
                    discord.SelectOption(label="Discord Suggestion", emoji="<:Discord:795240449103233024>", value="discord"),
                    discord.SelectOption(label="Hotel Suggestion", emoji="🏨", value="hotel"),
                    discord.SelectOption(label="Training Center Suggestion", emoji="<:studio:639558945584840743>", value="training"),
                    discord.SelectOption(label="Cancel Command", emoji="❌", value="cancel")
                ]
                
                select = Select(placeholder="Choose the type of your suggestion...", options=options)

                # This View is responsible for handling the select menu interaction
                class SuggestionView(View):
                    def __init__(self, *args, **kwargs):
                        super().__init__(*args, **kwargs)

                    @discord.ui.select(placeholder="Choose the type of your suggestion...", options=options)
                    async def select_callback(self, select, interaction: discord.Interaction):
                        # The selected value is available on select.values
                        selected_value = select.values[0]
                        
                        # Create embed for the suggestion
                        suggestEmbed = discord.Embed(description=suggestion, color=self.bot.main_color)
                        suggestEmbed.set_footer(text="Vinns Hotel Suggestions | -suggest")
                        suggestEmbed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)

                        if selected_value == "discord":
                            await discChannel.send(content=f"<@!{interaction.user.id}>", embed=suggestEmbed)
                            await interaction.response.edit_message(content="✅ | Successfully sent your suggestion to <#{}>".format(discChannel.id))
                        elif selected_value == "hotel":
                            await hotelChannel.send(content=f"<@!{interaction.user.id}>", embed=suggestEmbed)
                            await interaction.response.edit_message(content="✅ | Successfully sent your suggestion to <#{}>".format(hotelChannel.id))
                        elif selected_value == "training":
                            await trainingChannel.send(content=f"<@!{interaction.user.id}>", embed=suggestEmbed)
                            await interaction.response.edit_message(content="✅ | Successfully sent your suggestion to <#{}>".format(trainingChannel.id))
                        elif selected_value == "cancel":
                            await interaction.response.edit_message(content="❌ | Cancelled command.", embed=None)

                        # Disable the select menu after a choice is made
                        select.disabled = True
                        await interaction.message.edit(view=self)

                # Send the initial message with the select menu
                embed = discord.Embed(
                    description=f"**Select the type of your suggestion:**",
                    color=self.bot.main_color
                )
                embed.set_footer(text="Vinns Hotel Suggestions | -suggest")
                embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)

                view = SuggestionView(timeout=60)  # View with a timeout of 60 seconds
                await ctx.send(embed=embed, view=view)

        except discord.ext.commands.CommandOnCooldown:
            print("cooldown")


async def setup(bot):
    await bot.add_cog(Suggest(bot))
