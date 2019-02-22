# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.3'
#       jupytext_version: 1.0.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

import requests
from datetime import datetime as dt
from bs4 import BeautifulSoup as sp

# urls
itemsJson = "https://roexplorer.com/pricing/items.json"
oneItem = "https://search.roexplorer.com/item_price?id={}"
weeklyPrice = "https://search.roexplorer.com/pricing?interval=week"
monthlyPrice = "https://search.roexplorer.com/pricing?interval=month"

itemId = "41217"

r = requests.get(oneItem.format(itemId))

js = r.json()
js

# Get item list to know item ids
rr = requests.get(itemsJson)
items = rr.json()

search = "mystery bow"


def get_item_id(search,items):
    # Search equip
    itemId = 999999
    for item in items:
        name = item["name"]
        name = name.lower()
        search = search.lower()
        if search in name:
            print(item)
            iId = int(item['id'])
            if iId < itemId:
                itemId = int(iId)
    return itemId


def get_recipe(itemId):
    # Get roguard recipe
    recipeUrl = "https://www.roguard.net/db/items/{}".format(itemId)
    rec = requests.get(recipeUrl)
    soup = sp(rec.content,"lxml")
    tb = soup.find_all('tbody')
    return tb


def get_cells(rows):
    dic = {}
    for i in range(len(rows)):
        if i%2:
            cells = rows[i].find_all('span')
            for cell in cells:
                recipeId = cell.find('a').get('href').split('/')[3]
                quantity = int(cell.get_text().split('×')[0].replace(',',''))
                # if new id
                if not recipeId in dic.keys():
                    dic[recipeId] = quantity
                else:
                    dic[recipeId] = dic[recipeId] + quantity
    return dic


# +
def get_item_name(itemId):
    # Get item name from id
    itemUrl = "https://www.roguard.net/db/items/{}/".format(itemId)
    r = requests.get(itemUrl)
    s = sp(r.content,'lxml')
    displayName = s.find('h1').get_text()

    # Cross check with poporing.life display names
    headers = {"Origin": "https://poporing.life"}
    url = "https://api.poporing.life/get_item_list"
    r = requests.get(url,headers=headers)
    items=r.json()['data']['item_list']

    for item in items:
        disp = item['display_name']
        if displayName == disp:
            itemName = item['name']
    
    return itemName

def get_item_price(itemName):
    # Get latest price of item
    priceUrl = "https://api.poporing.life/get_latest_price/{}".format(itemName)
    headers = {"Origin": "https://poporing.life"}
    r = requests.get(priceUrl,headers=headers)
    price = r.json()['data']['data']['price']
    return itemId,itemName,price

def price_from_id(itemId):
    # Get price when buying the item
    itemName = get_item_name(itemId)
    idd,name,price = get_item_price(itemName)
    return price


# +
def get_total_price(dic,currBasePrice):
    # Get total price of upgrading item
    total = int(dic['100']) + currBasePrice
    breakdown = {'zenny':int(dic['100'])}
    
    for itemId in dic.keys():
        if not itemId == '100':
            itemName = get_item_name(itemId)
            idd,name,price = get_item_price(itemName)
            # Get price breakdown to know which component is the most expensive
#             print(name,itemId,price)
            breakdown[name] = dic[itemId] * price

            # Get total price
            total += dic[itemId] * price
    return breakdown,total

def compare_prices(itemId,totalCraft):
    name = get_item_name(itemId)
    priceBuy = price_from_id(itemId)
    priceCraft = totalCraft
    diff = abs(priceBuy-priceCraft)
    print("The price of {} is currently {} while the total craft price is at {}. Price difference is {}.".format(name,priceBuy,priceCraft,diff))

    
# -

# %%time
if __name__ == "__main__":
    userInput = input("Search equipment you want to check: ")
    # Check item json
    itemsJson = "https://roexplorer.com/pricing/items.json"
    
    # Get item list to know item ids
    rr = requests.get(itemsJson)
    items = rr.json()
    startItemId = get_item_id(userInput,items) # Starting id
    
    # If upgrade of, get the previous upgrade's current price at exchange as init price
    currBasePrice = 0
    tables = get_recipe(startItemId)

    # Check if upgrade of
    isUpgrade = tables[0].find("td",text="Upgrade Of")
    if isUpgrade is not None:
#         print ("May previous")
        # Get item id of prev
        itemId = tables[0].find_all('tr')[-1].find('a').get('href').split('/')[3]
#         print(itemId)
        tables = get_recipe(itemId)
        table = tables[1]
        rows = table.find_all('tr')
        
        # Get current price of initial item
        currBasePrice = price_from_id(itemId)

    else:
        table = tables[1]
        rows = table.find_all('tr')
#         print("Final")
    dic = get_cells(rows)
    breakdown,totalCraft = get_total_price(dic,currBasePrice)
    
    # Now is it better to craft or to buy?
    compare_prices(startItemId,totalCraft)


import pandas as pd

df = pd.DataFrame([breakdown])
df = df.transpose()
df.rename(columns={0:'price'},inplace=1)
df.sort_values(by=['price'],ascending=0,inplace=True)

df['% of total'] = round((df.price/totalCraft)*100,2)

df
