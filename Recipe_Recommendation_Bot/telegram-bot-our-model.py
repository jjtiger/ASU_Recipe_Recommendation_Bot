# importing the required libraries for telegram

from dotenv import load_dotenv
import os
from telegram.ext import Updater, Filters, CommandHandler, MessageHandler
from bs4 import BeautifulSoup
import random
import requests as rq
import json
from recipe_scrapers import scrape_me
from tensorflow.keras.preprocessing import image_dataset_from_directory
import pickle
import pandas as pd
from tensorflow import keras

model = keras.models.load_model(
    '../Jay-branch/model_veg_fruits')

# creating the updater instance to use our bot api key

load_dotenv()
telegram_api = os.getenv("telegram-api")
updater = Updater(telegram_api)
dispatcher = updater.dispatcher

# Define all the different commands to be used by the bot

# welcome message /start


def start(updater, context):
    updater.message.reply_text(
        'Welcome to our Beta Chef bot! We are still in Beta so please bear with us on our image recognition and recipe recomendation system \ntype /help to see a list of instructions on how to use our bot')

# help command with instructions on how the bot works /help


def helper(updater, context):
    updater.message.reply_text(
        'This works in two ways \n 1. Send it an image of some ingredients and it will attempt to recognize whats in the image \n 2.Send a list of 2 or more ingredients separated by a comma (,) and it will look up a random recipe from Allrecipes.com')

# instance to wait for any image sent to attempt and classify it using the model loaded above


# Creating an empty list to store the image labels the user sends after predictions
image_ingredients_from_user = []

# A function to append a var to out list , this is used to call from whithin another function below


def makelist(label):
    image_ingredients_from_user.append(label)

# Function to process the photo the user send and store it in the server or pc running the app


def process_photo(updater, context):
    photo = updater.message.photo[-1].get_file()
    photo.download('test_image/class1/img.jpg')
    # calling the keras module to create a dataframe for testing to be plugged into the model prediction method
    test_image_df = image_dataset_from_directory(
        directory='test_image',
        labels='inferred',
        label_mode='categorical',
        seed=5,
        color_mode="rgb",
        shuffle=True,
        batch_size=32,
        image_size=(100, 100)
    )
    # loading the label classes ( this part is static as the model is already trained)
    labels_df = pd.read_csv('labels_36.csv')

    # making the predictions based on the created test image df above
    label = labels_df.iloc[model.predict(test_image_df).argmax()]
    label = label.ingredient
    makelist(label)
    updater.message.reply_text(
        f'You sent an image of what seems to be : {label} .  Since we are in beta please send another item to predict or write a list of ingredients for me \n you can at any time type /reset to start over fresh')
    updater.message.reply_text(
        f'your list contains {image_ingredients_from_user} Once you are ready type /RecipeMe to see the results !')
# instance that takes the user text input and then scrapes the all recipes website to return a randoom recipe
# this is utilizes a python module developed by @hhursev  from https://github.com/hhursev/recipe-scrapers


def RecipeMe(updater, context):
    updater.message.reply_text(
        'let me suggest some foods for you based on your images')
    # webscraping workflow to get the base URL for allrecipes.com and append our predictions to it
    sentence = "&IngIncl="
    http_start = 'https://www.allrecipes.com/search/results/?search='

    # creating a local copy of the image list from the user
    image_ingredients = image_ingredients_from_user.copy()

    image_ingredients = [sentence + i for i in image_ingredients]
    image_ingredients = ''.join(image_ingredients)
    image_ingredients
    url = http_start + image_ingredients

    request = rq.get(url)

    soup = BeautifulSoup(request.text, 'html.parser')

    recipes = []

    for a in soup.find_all('a', href=True):
        recipes.append(a['href'])

    recipes_df = pd.DataFrame(recipes)
    recipes_df.columns = ['url']
    recipes_df = recipes_df.loc[recipes_df['url'].str.contains('/recipe/')]
    recipes_df.reset_index(inplace=True)
    import random
    random = random.randint(0, len(recipes_df))
    scrape = scrape_me(recipes_df['url'][random])
    title = scrape.title()

    instructions = scrape.instructions()
    pic = scrape.image()

    updater.message.reply_text(
        f'You can make ** {title} ** with you list provided and here is how to make it: \n{instructions}')
    updater.message.reply_photo(pic)
    print(f'user input was {image_ingredients}')
    print(f'the site :{url} was used')


def get_response(updater, context):
    updater.message.reply_text(
        'let me suggest some foods for you based on what you sent')
    text = updater.message.text
    ingredients = text.split(',')

    # webscraping workflow to get the base URL for allrecipes.com and append our predictions to it
    sentence = "&IngIncl="
    http_start = 'https://www.allrecipes.com/search/results/?search='

    ingredients = [sentence + i for i in ingredients]
    ingredients = ''.join(ingredients)
    ingredients
    url = http_start + ingredients

    request = rq.get(url)

    soup = BeautifulSoup(request.text, 'html.parser')

    recipes = []

    for a in soup.find_all('a', href=True):
        recipes.append(a['href'])

    recipes_df = pd.DataFrame(recipes)
    recipes_df.columns = ['url']
    recipes_df = recipes_df.loc[recipes_df['url'].str.contains('/recipe/')]
    recipes_df.reset_index(inplace=True)
    import random
    random = random.randint(0, len(recipes_df))
    scrape = scrape_me(recipes_df['url'][random])
    title = scrape.title()

    instructions = scrape.instructions()
    pic = scrape.image()

    updater.message.reply_text(
        f'You can make ** {title} ** with you list provided and here is how to make it: \n{instructions}')
    updater.message.reply_photo(pic)
    print(f'user input was {ingredients}')
    print(f'the site :{url} was used')

# Function to reset the image_ingredient list to for the user to input new ingiredints


def reset(updater, context):
    image_ingredients_from_user.clear()


# dispatchers for the various commands and listeners from within the telegram bot
dispatcher.add_handler(CommandHandler('Start', start))
dispatcher.add_handler(CommandHandler('Help', helper))
dispatcher.add_handler(CommandHandler('Reset', reset))
dispatcher.add_handler(CommandHandler('RecipeMe', RecipeMe))

dispatcher.add_handler(MessageHandler(Filters.photo, process_photo))
dispatcher.add_handler(MessageHandler(Filters.text, get_response))

# starting the telegram bot instance and wating for the commands

updater.start_polling()
updater.idle()
