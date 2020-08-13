import robin_stocks as r
import pandas as pd
from datetime import datetime
import numpy as np
import requests_cache
import pandas_datareader as pdr
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv
import glob

# 1. Import environment variables and login to Robinhood account

load_dotenv()
username = os.environ.get("robinhood-username")
password = os.environ.get("robinhood-password")

login = r.login(username, password)
print('login successful!!\n')

# 2. Get list of all stock orders and create Dataframe

print('getting all stock orders...\n')
orders = r.get_all_stock_orders()

tickers_list = []
shares_list = []
avg_price_list = []
dates_list = []

for i in range(len(orders)):
    # Exclude failed orders
    if orders[i]['state'] != 'filled':
        continue
    
    # Get stock ticker associated with the order
    instrument = orders[i]['instrument']
    symbol = r.get_symbol_by_url(instrument)
    tickers_list.append(symbol)


    shares = orders[i]['cumulative_quantity']
    # We want shares to be negative if the order was a sell
    if orders[i]['side'] == 'sell':
        shares_list.append(float(shares) * -1)
    else:
        shares_list.append(float(shares))

    avg_price = orders[i]['average_price']
    avg_price_list.append(float(avg_price))

    date_object = datetime.strptime(orders[i]['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ').date()
    dates_list.append(date_object)

# I got historical stock prices from Yahoo but need to edit this stock ticker for it to work
tickers_list = [ ticker if ticker != 'BRK.B' else 'BRK-B' for ticker in tickers_list ]
print('creating orders dataframe...\n')
# Create a dataframe
all_orders = pd.DataFrame(list(zip(tickers_list, shares_list, avg_price_list, dates_list)), columns=['ticker', 'shares_bought', 'avg_price_per_share', 'date_of_transaction'])
# Add column 'order_amount' which equals shares bought times average price per share
all_orders['order_amount'] = all_orders['shares_bought'] * all_orders['avg_price_per_share']
# Reverse the order of rows so that the first row is the earliest order by date
# Use df.sort_values instead
all_orders = all_orders.reindex(index=all_orders.index[::-1]).reset_index(drop=True)
# Add column 'total_amount_bought' which is the cumulative sum of all orders to that point in time
all_orders['total_amount_bought'] = all_orders['order_amount'].cumsum()
print('exporting orders dataframe to csv...\n')
# Export data frame to a csv to avoid calling API repeatedly
all_orders.to_csv('all_orders.csv', index=False)

# 3. Create a dataframe of just buy orders
buy_orders = all_orders[all_orders['shares_bought'] > 0].reset_index(drop=True)
buy_orders['total_amount_bought'] = buy_orders['order_amount'].cumsum()
print('exporting buy orders dataframe to csv...\n')
# get rid of that first unnamed column
# Edit the BRK.B entry
buy_orders.to_csv('robinhood_buy_orders.csv', index=False)

# 4. This section gets historical price data for all stocks that I have purchased at one point an creates a csv
# Get rid of ticker duplicates
tickers_list_filtered = list(dict.fromkeys(tickers_list))
start_date = datetime(2019, 1, 17)
end_date = datetime(2020, 8, 7)

# Individual csv's will be combined for easier and quicker manipulation and you don't have to continuously call the API
for stock in tickers_list_filtered:
    print('Creating csv for', stock)
    price_data = pdr.get_data_yahoo(stock, start_date, end_date)
    price_data['Ticker'] = stock
    price_data.to_csv('/Users/aidanhall/Desktop/python/stock_data/' + stock + '.csv')

# The following code combines csv's of historical prices
print('Combining csvs')
os.chdir('/Users/aidanhall/Desktop/python/stock_data')
print('Changed directory...')

extension = 'csv'
all_filenames = [i for i in glob.glob('*.{}'.format(extension))]
combined_csv = pd.concat([pd.read_csv(f) for f in all_filenames])
combined_csv.to_csv('../all_positions_price_data.csv', index=False)

os.chdir('/Users/aidanhall/Desktop/python')
print('Changed back..')
price_data = pd.read_csv('all_positions_price_data.csv')
print(price_data.head())
##
all_orders = pd.read_csv('all_orders.csv')
buy_orders = pd.read_csv('robinhood_buy_orders.csv')
# 5. Create the range of dates list 
print('Creating date range list...\n')
remove_duplicate_dates = price_data.drop_duplicates(subset='Date')
trading_days = remove_duplicate_dates['Date']
trading_days_list = trading_days.tolist()
print(trading_days_list)
### Tried initially to create a weekly date range starting from the account start date
### to the present however some days fell on non-trading days (weekend and holidays)
### and that messed up some calculations having to do with closing price of a stock at a particular date
### ended up just using a daily date range of trading days retrieved from yahoo api from pandas datareader

# 6. Create a list that has the cumulative total amount of deposits made over each trading day

# All orders
date_amount_tuple = list(zip(all_orders['date_of_transaction'].tolist(), all_orders['total_amount_bought'].tolist()))
date_amount_dict = dict(date_amount_tuple)
print(date_amount_dict)
actual_total_deposits = []

# for each trading day, check if there was a transaction that change the total amount bought
# otherwise the total amount bought should equal what it was the previous day
for day in trading_days_list:
    try:
        actual_total_deposits.append(date_amount_dict[day])
    except KeyError:
        actual_total_deposits.append(actual_total_deposits[-1])

print('Actual account cumulative deposits:\n', actual_total_deposits)

# 7. Create a list that has the cumulative total deposits for buy orders made over each trading day

buy_orders_tuple = list(zip(buy_orders['date_of_transaction'].tolist(), buy_orders['total_amount_bought'].tolist()))
buy_orders_dict = dict(buy_orders_tuple)

total_buy_deposits = []

for day in trading_days_list:
    try:
        total_buy_deposits.append(buy_orders_dict[day])
    except KeyError:
        total_buy_deposits.append(total_buy_deposits[-1])

print('Only buy orders cumulative deposits:\n', total_buy_deposits)

## 8. Create a list over each trading day for the total value of the portfolio assuming shares were never sold

nosell_value_list = []

for i in range(len(trading_days_list)):
    transactions = buy_orders.loc[buy_orders['date_of_transaction'] <= trading_days_list[i]]
    group_by_ticker = transactions.groupby('ticker').shares_bought.sum().reset_index()
    total_value_at_date = 0
    
    for ind in group_by_ticker.index:
        stock = group_by_ticker['ticker'][ind]
        price_at_date = price_data.loc[(price_data['Date'] == trading_days_list[i]) & (price_data['Ticker'] == stock)]
        closing_price = price_at_date['Adj Close']
        total_stock_value = closing_price * group_by_ticker['shares_bought'][ind]
        total_value_at_date += float(total_stock_value)
    nosell_value_list.append(total_value_at_date)

print('Value of nosell portfolio:\n', nosell_value_list)

## 9. Total value of actual portfolio

actual_value_list = []

for i in range(len(trading_days_list)):
    transactions = all_orders.loc[all_orders['date_of_transaction'] <= trading_days_list[i]]
    group_by_ticker = transactions.groupby('ticker').shares_bought.sum().reset_index()
    total_value_at_date = 0

    for ind in group_by_ticker.index:
        stock = group_by_ticker['ticker'][ind]
        price_at_date = price_data.loc[(price_data['Date'] == trading_days_list[i]) & (price_data['Ticker'] == stock)]
        closing_price = price_at_date['Adj Close']
        total_stock_value = closing_price * group_by_ticker['shares_bought'][ind]
        total_value_at_date += float(total_stock_value)
    actual_value_list.append(total_value_at_date)

print('value of actual portfolio\n', actual_value_list)

## 10. Calculate rate of returns for nosell portfolio

daily_rate_of_return_nosell = []
for i in range(len(trading_days_list)):
    end_of_day_value = nosell_value_list[i]
    start_of_day_value = (nosell_value_list[i-1] if i > 0 else total_buy_deposits[i]) + (total_buy_deposits[i] - total_buy_deposits[i-1] if i > 0 else 0)
    daily_rate_of_return_nosell.append(1 + ((end_of_day_value - start_of_day_value) / start_of_day_value))

cumulative_geometric_avg_return_nosell = [(np.prod(daily_rate_of_return_nosell[:i + 1]) - float(1)) for i in range(len(daily_rate_of_return_nosell))]

print('cumulative geo avg return no sell portfolio\n', cumulative_geometric_avg_return_nosell)

## 11. Calculate rate of returns for actual portfolio

daily_rate_of_return_actual = []
for i in range(len(trading_days_list)):
    end_of_day_value = actual_value_list[i] 
    start_of_day_value = (actual_value_list[i-1] if i > 0 else actual_total_deposits[i]) + (actual_total_deposits[i] - actual_total_deposits[i-1] if i > 0 else 0)
    daily_rate_of_return_actual.append(1 + ((end_of_day_value - start_of_day_value) / start_of_day_value))

cumulative_geometric_avg_return_actual = [(np.prod(daily_rate_of_return_actual[:i + 1]) - float(1)) for i in range(len(daily_rate_of_return_actual))]

print('cumulative geo avg return actual portfolio\n', cumulative_geometric_avg_return_actual)

return_info = pd.DataFrame(list(zip(trading_days_list, actual_total_deposits, total_buy_deposits, nosell_value_list, actual_value_list, cumulative_geometric_avg_return_actual, cumulative_geometric_avg_return_nosell)), columns=['dates', 'actual deposits', 'buy order deposits', 'no sell value', 'actual value', 'actual return', 'no sell return'])


return_info.to_csv('return_info.csv', index=False)



