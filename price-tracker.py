#imports
from pymongo import MongoClient
import pprint
from bs4 import BeautifulSoup
from lxml import etree
import requests
from datetime import datetime
from tkinter import *
import matplotlib.pyplot as plt

HEADERS = ({'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',\
            'Accept-Language': 'en-US, en;q=0.5'})

date = datetime.today().strftime('%Y-%m-%d')

def convertPrice(price):
    convertedPrice = ""
    for i in price[:price.index(".")]:
        if (i in ['0','1','2','3','4','5','6','7','8','9']):
            convertedPrice += i
    return convertedPrice

def getDetailsFromURL(URL):
    try:
        webpage = requests.get(URL, headers=HEADERS)
        soup = BeautifulSoup(webpage.content, "html.parser")
        dom = etree.HTML(str(soup))
        
        productTitle = dom.xpath('//*[@id="productTitle"]')[0].text.strip()
        price = dom.xpath('//*[@id="priceblock_ourprice"]')[0].text[2:]
        price = convertPrice(price)
        
        return {'title': productTitle, 'price': price}
    except:
        return None

def connectToDatabase():
    try:
        client = MongoClient()
        db = client.test
        products = db.Products
        return {'client': client, 'products': products}
    except:
        return None

def fetchDataFromDatabase(products, productName, price, URL):
    doc = products.find_one( { 'productName': productName} )
    if(doc):
        doc.get("price").update( {date : int(price)} )
        products.replace_one({ 'productName': doc.get("productName") }, doc )
        priceValues = doc.get("price")
    else:
        new_product = {
            "productName": productName,
            "URL": URL,
            "price":{
                date : int(price)
            }
        }
        products.insert_one(new_product)
        priceValues = {date: price}
        print("It Seems The Current Product Doesn't Exist In Our Database. Don't worry we have updated it.")
    return priceValues

def buttonclick(URL, welcomeLabel):
    try:
        details = getDetailsFromURL(URL)
        if(details == None):
            raise FetchException
        productName = details['title']
        price = details['price']

        db = connectToDatabase()
        if(db == None):
            raise DatabaseConnectivityException
        client = db['client']
        products = db['products']

        priceValues = fetchDataFromDatabase(products, productName, price, URL)
        
        graphDateValues = list(priceValues.keys())
        graphPriceValues = list(priceValues.values())

        plt.plot(graphDateValues, graphPriceValues)
        plt.title('Price History')
        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.xticks(rotation=30)
        plt.show()

    except FetchException:
        welcomeLabel.configure(text="Error Fetching Data From URL", fg="red")
    except DatabaseConnectivityException:
        welcomeLabel.configure(text="Error Connecting To Database", fg="red")
    except FetchFromDatabaseException:
        welcomeLabel.configure(text="Error Fetching Records From Database", fg="red")
    except:
        welcomeLabel.configure(text="Something Went Wrong", fg="red")


class FetchException(Exception):
    """Raised when there is a problem while fetching data"""
    pass

class DatabaseConnectivityException(Exception):
    """Raised when there is a problem connecting to Database"""
    pass

class FetchFromDatabaseException(Exception):
    """Raised when there is a problem fetching data from a database"""
    pass

def main():    
        root = Tk()

        welcomeLabel = Label(root, text = "Welcome, Enter the URL to get price history")
        welcomeLabel.grid(row = 0, column = 0, padx = 10, pady = 10)
        inputField = Entry(root, width = 50 , borderwidth = 3)
        inputField.grid(row = 1, column = 0, padx = 10, pady = 10)
        button = Button(root, text = "Submit", width = 40, command = lambda: buttonclick(inputField.get(), welcomeLabel))
        button.grid(row = 2, column = 0, padx = 10, pady = 10)
        
        root.mainloop()
       
if __name__ == "__main__":
    main()