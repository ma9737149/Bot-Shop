import discord,random
from discord.ext import commands
import sqlite3,asyncio
from config import TOKEN
from discord import app_commands

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())
tree = client.tree


@client.event
async def on_ready():
    syncedCommands = await tree.sync()



    db = sqlite3.connect("products.db")
    cursor = db.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS products(guild_id INTEGER , price INTEGER , product_name VARCHAR , products VARCHAR)")
    db.commit()
    db.close()
    # -----------
    db2 = sqlite3.connect("owner.db")
    cur2 = db2.cursor()

    cur2.execute(
        "CREATE TABLE IF NOT EXISTS user(guild_id INTEGER , user_id INTEGER)")
    db2.commit()
    db2.close()



    print(f'synced {len(syncedCommands)} command(s)')


@tree.command(name="setup", description="takes the user to send it the credits")
@app_commands.describe(user="who user you wanna transfare to it")
async def _setup(interaction: discord.Interaction, user: discord.Member):
    if interaction.user.guild_permissions.administrator:
        if user.bot:
            await interaction.response.send_message("You can't transfer credits to a bot" , ephemeral=True)
            return

        db = sqlite3.connect("owner.db")
        cur = db.cursor()
        cur.execute("SELECT user_id FROM user WHERE guild_id = ?",(interaction.guild.id,))
        user_data = cur.fetchone()

        

        if user_data:
            if user_data[0] == user.id:
                await interaction.response.send_message("This user is already the transfare user" , ephemeral=True)
                return
            cur.execute("UPDATE user SET user_id = ? WHERE guild_id = ?",(user.id, interaction.guild.id))
            db.commit()
            db.close()
            await interaction.response.send_message(f"transfare user has been changed to <@{user.id}>")
            return
        

        cur.execute("INSERT INTO user VALUES(? , ?)",
                    (interaction.guild.id, user.id))
        db.commit()
        db.close()

        await interaction.response.send_message(f"transfare user has been set to <@{user.id}>")
    else:
        await interaction.response.send_message("You can't transfer credits to a non-admin user" , ephemeral=True)



@tree.command(name = "add_product" , description= "add product into the stock")
@app_commands.describe(product_name="what is the product name?" , price="what it the price?" ,  products_you_have="what products you have ? write it with this pattern -> product1,product2,product3")
async def _add_product(interaction:discord.Interaction , product_name : str , price :int ,products_you_have : str):
    if interaction.user.guild_permissions.administrator:

            db = sqlite3.connect("products.db")
            cur = db.cursor()

            cur.execute("SELECT product_name FROM products WHERE product_name = ? AND guild_id = ?",(product_name.lower(),interaction.guild.id))
            data = cur.fetchone()

            if data:
                await interaction.response.send_message("this product it allready exists" , ephemeral=True)
                db.close()
                return
            else:
                cur.execute("INSERT INTO products VALUES(?,?,?,?)",(interaction.guild.id, price , product_name.lower(),products_you_have))
                db.commit()
                db.close()
                await interaction.response.send_message("product added" , ephemeral=True)

    else:
        await interaction.response.send_message("You don't have permission to use this command" , ephemeral=True)

def get_data(guild_id : int) -> list:
    db = sqlite3.connect("products.db")
    cr = db.cursor()
    cr.execute("SELECT product_name FROM products WHERE guild_id = ?", (guild_id,))
    data = cr.fetchall()
    db.close()



    return [product[0] for product in data]


async def product_autocompete(interaction:discord.Interaction,current:str):
    data = get_data(interaction.guild.id)
    return [app_commands.Choice(name=productName,value=productName) for productName in data]


@tree.command(name = "edit_product" , description="edit product from stock")
@app_commands.autocomplete(product_name = product_autocompete)
@app_commands.describe(product_name = "enter the product name" , price = "enter the product price" , products = "enter the products separated by comma")
async def _edit_product(interaction:discord.Interaction , product_name : str , new_name : str, price : int, products:str):
    if interaction.user.guild_permissions.administrator:
        if not product_name.lower() in get_data(interaction.guild.id):
            await interaction.response.send_message("this product it not in stock" , ephemeral=True)
            return

        db = sqlite3.connect("products.db")
        cur = db.cursor()

        cur.execute("UPDATE products SET product_name = ? , price = ? , products = ? WHERE guild_id = ? AND product_name = ?",(new_name.lower(),price,products,interaction.guild.id,product_name.lower()))
        db.commit()
        db.close()

        await interaction.response.send_message("product updated" , ephemeral=True)

    else:
        await interaction.response.send_message("You can't use this commands because it's for admins only" , ephemeral=True)






@tree.command(name = "remove_product" , description="remove product from stock")
@app_commands.autocomplete(product_name=product_autocompete)
@app_commands.describe(product_name = "choose from these products")
async def _remove_product(interaction:discord.Interaction , product_name:str):
    if interaction.user.guild_permissions.administrator:
        if not product_name.lower() in get_data(interaction.guild.id):
            await interaction.response.send_message("this product it not in stock" , ephemeral=True)
            return

        db = sqlite3.connect("products.db")
        cur = db.cursor()
        cur.execute("DELETE FROM products WHERE product_name = ? AND guild_id = ?" , (product_name.lower(),interaction.guild.id))
        db.commit()
        db.close()
        await interaction.response.send_message(f'{product_name} removed', ephemeral=True)
    else:
        await interaction.response.send_message("You can't use this commands because it's for admins only" , ephemeral=True)




@tree.command(name = "stock" , description = "show the current stock")
async def _stock(interaction : discord.Interaction):
    db = sqlite3.connect("products.db")
    cur = db.cursor()
    cur.execute("SELECT  product_name , price , products FROM products WHERE guild_id = ?" , (interaction.guild.id,))
    data = cur.fetchall()

    if data:
        embed = discord.Embed(title="Stock:" , description="" , color=discord.Color.dark_gold())
        for i in data:
            count = len(i[2].split(","))
            embed.add_field(name= i[0].title() , value=f"count : {count}\nprice : {i[1]}" , inline=False)
        
        embed.set_author(name=interaction.guild.name,icon_url=interaction.guild.icon)
        embed.set_footer(text=f"requested by : {interaction.user.display_name}" , icon_url=interaction.user.display_avatar)

        await interaction.response.send_message(embed = embed)
    else:
        embed = discord.Embed(title="" , description="theres is not products to sell" , color=discord.Color.red())
        await interaction.response.send_message(embed = embed)


@tree.command(name = "buy" , description="buy a product from the stock")
@app_commands.describe(product_name="the product name you want to buy" , quantity = "quantity u wanna buy")
@app_commands.autocomplete(product_name = product_autocompete)
async def _buy(interaction:discord.Interaction,product_name:str,quantity:int=1):
    ow_db = sqlite3.connect("owner.db")
    ow_cur = ow_db.cursor()

    ow_cur.execute("SELECT user_id FROM user WHERE guild_id = ?" , (interaction.guild.id,))

    ow_data = ow_cur.fetchone()

    ow_db.close()

    if ow_data:
        if product_name.lower() in get_data(interaction.guild.id):

            db = sqlite3.connect("products.db")
            cur = db.cursor()
            cur.execute("SELECT products,price FROM products WHERE product_name = ? AND guild_id = ?" , (product_name.lower(),interaction.guild.id))
            data = cur.fetchone()
            products = data[0]
            price = data[1]
            count = len(products.split(","))

            if quantity > count:
                db.close()
                await interaction.response.send_message("you can't buy quantity is larger than item quantity" , ephemeral=True)
                return

            random_products = random.sample(products.split(","),k=quantity)
            
            await interaction.response.send_message("do the instructions", ephemeral=True)

            my_Msg = await interaction.channel.send(f"{interaction.user.mention} transfare `{int((price*quantity)//0.95 + 1)}` to <@{ow_data[0]}>\nWaiting for 60 seconds...")

            def check(msg):
                return msg.author.id == 282859044593598464 and msg.guild.id == interaction.guild.id and msg.channel.id == interaction.channel.id and msg.content == f"**:moneybag: | {str(interaction.user)}, has transferred `${int((price*quantity))}` to <@!{ow_data[0]}> **"

            try:
                message = await client.wait_for("message" , check=check , timeout=60)
                

                if message:
                    current_products = ",".join([x for x in products.split(",") if x not in random_products])
                    if current_products != "":
                        cur.execute("UPDATE products SET products = ? WHERE product_name = ? AND guild_id = ?" , (current_products,product_name.lower(),interaction.guild.id))
                        db.commit()
                        db.close()

                    else:
                        cur.execute("DELETE FROM products WHERE product_name = ? AND guild_id = ?" , (product_name.lower(),interaction.guild.id))
                        db.commit()
                        db.close()

                    await interaction.user.send(f"you got\n{','.join(random_products)}")
                    await my_Msg.edit(content = f"{interaction.user.mention} the product sent")

            except asyncio.TimeoutError:
                db.close()
                await my_Msg.edit(content=f"{interaction.user.mention} you didn't transfare")



        else:
            await interaction.response.send_message("this product is not in the stock" , ephemeral=True)

    else:
        await interaction.response.send_message("you can't use this command because there is no owner id to use this command u should add owner id by setup command (you should be administrator to use it)" , ephemeral=True)




client.run(TOKEN)
