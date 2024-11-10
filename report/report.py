import discord
from discord.ext import commands
from core import checks
from core.models import PermissionLevel
import asyncio


class Reports(commands.Cog):
    """
    Easy report system with multiple proof uploads and checkmark to confirm.
    """

    def __init__(self, bot):
        self.bot = bot
        self.coll = bot.plugin_db.get_partition(self)

    @commands.command()
    @checks.has_permissions(PermissionLevel.REGULAR)
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def report(self, ctx):
        """
        Report a player with the ability to provide multiple pieces of proof.
        """
        try:
            staffChannel = self.bot.get_channel(686253307278393442)
            guestChannel = self.bot.get_channel(686253328270884877)
            if ctx.guild.id == 814758983238942720:
                staffChannel = self.bot.get_channel(818446997816082432)
                guestChannel = self.bot.get_channel(818447055810199552)
            
            texta = """**React with the type of your report:**
  1️⃣ | Staff Report
  2️⃣ | Guest Report
  ❌ | Cancel
  """

            embedTimeout = discord.Embed(description="❌ | You took too long! Command cancelled", color=15158332)
            embed1 = discord.Embed(description=texta, color=self.bot.main_color)
            embed1.set_footer(text="React with ❌ to cancel")
            reactionmsg = await ctx.send(content=f"<@!{ctx.author.id}>", embed=embed1)
            for emoji in ('1️⃣', '2️⃣', '❌'):
                await reactionmsg.add_reaction(emoji)

            def checkmsg(msg: discord.Message):
                return msg.channel == ctx.channel and msg.author == ctx.author

            def cancel_check(msg: discord.Message):
                return msg.content.lower() == "cancel" or msg.content.lower() == f"{ctx.prefix}cancel"
            
            def check(r, u):
                return u == ctx.author

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=20.0, check=check)
            except asyncio.TimeoutError:
                return await reactionmsg.edit(embed=embedTimeout)

            if str(reaction.emoji) == '1️⃣':
                await reactionmsg.clear_reactions()

                # Collect the report details
                username = await self.ask_for_input(ctx, reactionmsg, "**Staff Report**\nWhat is the username of the user you're reporting?", 120)
                if username is None:
                    return
                rank = await self.ask_for_input(ctx, reactionmsg, "**Staff Report**\nWhat is the rank of the suspect?", 120)
                if rank is None:
                    return
                reason = await self.ask_for_input(ctx, reactionmsg, "**Staff Report**\nWhat is the reason for this report?", 120)
                if reason is None:
                    return

                # Proof upload loop
                proofs = []
                await reactionmsg.edit(embed=discord.Embed(description="**Staff Report**\nPlease provide proof of this happening. You can upload a video/image or use a link to an image or video. You can upload multiple files. React with ✅ when done. You have 10 minutes.", color=self.bot.main_color))
                
                def check_reaction(r, u):
                    return u == ctx.author and r.message.id == reactionmsg.id and str(r.emoji) in ('✅', '❌')

                try:
                    # Wait for a checkmark or cancel
                    while True:
                        message = await self.bot.wait_for('message', check=checkmsg, timeout=600)
                        if cancel_check(message):
                            return await self.cancel_report(reactionmsg)
                        # Save proof files
                        proofs.extend([await x.to_file() for x in message.attachments])
                        await message.delete()
                        
                        # After a proof is sent, check for a reaction to confirm completion
                        await reactionmsg.clear_reactions()
                        await reactionmsg.add_reaction('✅')
                        await reactionmsg.add_reaction('❌')
                        
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=600.0, check=check_reaction)

                        if str(reaction.emoji) == '✅':
                            break  # Done uploading proofs
                        elif str(reaction.emoji) == '❌':
                            return await self.cancel_report(reactionmsg)

                except asyncio.TimeoutError:
                    return await reactionmsg.edit(embed=embedTimeout)

                # Send report with the collected details and proofs
                reportEmbed = discord.Embed(title="New Staff Report", color=self.bot.main_color)
                reportEmbed.add_field(name="Username:", value=username)
                reportEmbed.add_field(name="Rank:", value=rank)
                reportEmbed.add_field(name="Reason:", value=reason)
                reportEmbed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
                if proofs:
                    await staffChannel.send(content="---------------------------", embed=reportEmbed, files=proofs)
                    text = "✅ | The report has successfully been sent!"
                    await reactionmsg.edit(embed=discord.Embed(description=text, color=3066993))

            elif str(reaction.emoji) == '2️⃣':
                await reactionmsg.clear_reactions()
            
                # Collect the report details for the Guest Report
                username = await self.ask_for_input(ctx, reactionmsg, "**Guest Report**\nWhat is the username of the user you're reporting?", 120)
                if username is None:
                    return
            
                reason = await self.ask_for_input(ctx, reactionmsg, "**Guest Report**\nWhat is the reason for this report?", 120)
                if reason is None:
                    return
            
                # Proof upload loop for Guest Report
                proofs = []
                await reactionmsg.edit(embed=discord.Embed(description="**Guest Report**\nPlease provide proof of this happening. You can upload a video/image or use a link to an image or video. You can upload multiple files. React with ✅ when done. You have 10 minutes.", color=self.bot.main_color))
            
                def check_reaction(r, u):
                    return u == ctx.author and r.message.id == reactionmsg.id and str(r.emoji) in ('✅', '❌')
            
                try:
                    # Wait for a checkmark or cancel
                    while True:
                        message = await self.bot.wait_for('message', check=checkmsg, timeout=600)
                        if cancel_check(message):
                            return await self.cancel_report(reactionmsg)
                        # Save proof files
                        proofs.extend([await x.to_file() for x in message.attachments])
                        await message.delete()
                        
                        # After a proof is sent, check for a reaction to confirm completion
                        await reactionmsg.clear_reactions()
                        await reactionmsg.add_reaction('✅')
                        await reactionmsg.add_reaction('❌')
                        
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=600.0, check=check_reaction)
            
                        if str(reaction.emoji) == '✅':
                            break  # Done uploading proofs
                        elif str(reaction.emoji) == '❌':
                            return await self.cancel_report(reactionmsg)
            
                except asyncio.TimeoutError:
                    return await reactionmsg.edit(embed=embedTimeout)
            
                # Send report with the collected details and proofs
                reportEmbed = discord.Embed(title="New Guest Report", color=self.bot.main_color)
                reportEmbed.add_field(name="Username:", value=username)
                reportEmbed.add_field(name="Reason:", value=reason)
                reportEmbed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
                if proofs:
                    await guestChannel.send(content="---------------------------", embed=reportEmbed, files=proofs)
                    text = "✅ | The report has successfully been sent!"
                    await reactionmsg.edit(embed=discord.Embed(description=text, color=3066993))


            elif str(reaction.emoji) == '❌':
                await self.cancel_report(reactionmsg)

        except discord.ext.commands.CommandOnCooldown:
            print("cooldown")

    async def ask_for_input(self, ctx, msg, prompt, timeout):
        """Helper function to ask for input from the user."""
        await msg.edit(embed=discord.Embed(description=prompt, color=self.bot.main_color))
        try:
            response = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=timeout)
            await response.delete()
            return response.content
        except asyncio.TimeoutError:
            await msg.edit(embed=discord.Embed(description="❌ | You took too long! Command cancelled", color=15158332))
            return None

    async def cancel_report(self, reactionmsg):
        """Helper function to handle report cancellation."""
        cancelEmbed = discord.Embed(description="❌ | Cancelled report", color=15158332)
        await reactionmsg.edit(embed=cancelEmbed)
        await reactionmsg.clear_reactions()

async def setup(bot):
    await bot.add_cog(Reports(bot))
