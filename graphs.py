import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import matplotlib.ticker as mtick

# Add some new columns
return_info = pd.read_csv('return_info.csv')
return_info['daily actual return'] = (return_info['actual value'] - (return_info['actual value'].shift() + return_info['actual deposits'] - return_info['actual deposits'].shift())) / (return_info['actual value'].shift() + return_info['actual deposits'] - return_info['actual deposits'].shift())
return_info['daily no sell return'] = (return_info['no sell value'] - (return_info['no sell value'].shift() + return_info['buy order deposits'] - return_info['buy order deposits'].shift())) / (return_info['no sell value'].shift() + return_info['buy order deposits'] - return_info['buy order deposits'].shift())


## Distribution of daily changes
sns.set_palette('Dark2')
sns.set_style('whitegrid')
sns.plotting_context(font_scale=1.5)
f, ax = plt.subplots(figsize=(12, 8))

sns.kdeplot(return_info['daily actual return'] * 100, shade=True)
sns.kdeplot(return_info['daily no sell return'] * 100, shade=True)

ax.set_yticklabels([''])
ax.xaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_xlabel('Daily Percent Change')
ax.legend(['Actual Portfolio', 'No Sell Portfolio'])
ax.set_title('Distribution of Daily Percent Change to Each Portfolio')

plt.savefig('dailychange.png')

## Deposits and Value over time

sns.set_style('whitegrid')
f1, ax1 = plt.subplots(figsize=(12, 8))


sns.lineplot(data=return_info, x='dates', y='actual deposits', color='#c2a5cf')
sns.lineplot(data=return_info, x='dates', y='actual value', color='#7b3294')


sns.lineplot(data=return_info, x='dates', y='buy order deposits', color='#a6dba0')
sns.lineplot(data=return_info, x='dates', y='no sell value', color='#008837')

ticks_list1 = list(range(0, len(return_info.dates.tolist()), 50))
day_labels1 = [return_info.dates.tolist()[ind] for ind in ticks_list1]
ax1.set_xticks(ticks_list1)
ax1.set_xticklabels(day_labels1)

fmt = '${x:,.0f}'
tick = mtick.StrMethodFormatter(fmt)
ax1.yaxis.set_major_formatter(tick)

ax1.set_xlabel('Trading Days')
ax1.set_ylabel('Portfolio Value')
ax1.set_title('Value of Actual and No Sell Portfolios Compared to Amount Deposited')
ax1.legend(['Actual Deposits', 'Actual Value', 'No Sell Deposits', 'No Sell Value'])

plt.savefig('valueovertime.png')

sns.set_style('darkgrid')

## Plot percent gain (value of $100) for never sell portfolio vs percent gain actual portfolio

return_info['value 100 actual'] = 100 * (1 + return_info['actual return'])
return_info['value 100 actual'] = return_info['value 100 actual'].shift() * (1 + return_info['daily actual return'])
return_info['value 100 no sell'] = 100 * (1 + return_info['no sell return'])
return_info['value 100 no sell'] = return_info['value 100 no sell'].shift() * (1 + return_info['daily no sell return'])

f5, ax5 = plt.subplots(figsize=(12, 8))
sns.lineplot(data=return_info, x='dates', y='value 100 actual')
sns.lineplot(data=return_info, x='dates', y='value 100 no sell')

ax5.yaxis.set_major_formatter(tick)
ax5.set_xlabel('Trading Days')
ax5.set_ylabel('Value')
ax5.set_title("Value of $100 Invested At Portfolios' Inception")
ax5.legend(['Actual Portfolio', 'No Sell Portfolio'])

ax5.set_xticks(ticks_list1)
ax5.set_xticklabels(day_labels1)

plt.savefig('value100.png')

## rolling cumulative returns vs. deposits

sns.set_style('dark')
f3, ax3 = plt.subplots(figsize=(12, 8))

lns1 = ax3.plot(return_info.dates, return_info['actual return'] * 100, color='#1b9e77', label='Cumulative Return')
ax3.set_xlabel('Trading Days')
ax3.set_ylabel('Cumulative Return (Actual Portfolio)')
plt.legend()

ax4 = ax3.twinx()
lns2 = ax4.plot(return_info.dates, return_info['actual deposits'], color='#d95f02', label='Cumulative Deposits')
ax4.set_ylabel('Total Deposits (Actual Portfolio)')


ax3.set_xticks(ticks_list1)
ax3.set_xticklabels(day_labels1)
ax3.yaxis.set_major_formatter(mtick.PercentFormatter())

ax4.yaxis.set_major_formatter(tick)
ax3.set_title('Comparing Cumulative Deposits to Cumulative Return of the Actual Portfolio')

lns = lns1 + lns2
labs = [l.get_label() for l in lns]
ax3.legend(lns, labs, loc=0)

plt.savefig('returnsToDeposits.png')


# Show all

plt.show()



