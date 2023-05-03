import yfinance as yf
from datetime import datetime,timedelta
import pandas as pd

def rsi(df, periods = 14, ema = True):
    """
    Returns a pd.Series with the relative strength index.
    """
    close_delta = df['Close'].diff()

    # Make two series: one for lower closes and one for higher closes
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)
    
    if ema == True:
	    # Use exponential moving average
        ma_up = up.ewm(com = periods - 1, adjust=True, min_periods = periods).mean()
        ma_down = down.ewm(com = periods - 1, adjust=True, min_periods = periods).mean()
    else:
        # Use simple moving average
        ma_up = up.rolling(window = periods).mean()
        ma_down = down.rolling(window = periods).mean()
        
    rsi = ma_up / ma_down
    rsi = 100 - (100/(1 + rsi))
    return rsi

tesla = yf.Ticker('TSLA')

days_to_subtract = [50*i for i in range(8)]
days_to_subtract.append(365)
dates = [datetime.now() - timedelta(days=subtracted_days) for subtracted_days in days_to_subtract]

histories = [tesla.history(start = dates[i+1],end = dates[i],interval = '1h').iloc[::-1] for i in list(range(len(dates)-1))]

# history = tesla.history(period='1y',interval='1h')

history = pd.concat(histories)

history['rsi'] = rsi(history,ema=False)
history['in_action'] = False

history = history.dropna().iloc[::-1]

def is_proper_4_action(rsi):
  p = [0]
  for i in range(len(rsi)-1):
    if rsi[i+1]<30 and rsi[i]>30:
      p.append(1)
    elif rsi[i+1]>50 and rsi[i]<50:
      p.append(-1)
    else:
      p.append(0)
  return p

history['is_proper_4_action'] = is_proper_4_action(history['rsi'])

def set_action(in_action,is_proper_4_action):
  proper_action = []
  for index,i in enumerate(zip(in_action,is_proper_4_action)):
    if i[0] == False and i[1]==1:
      proper_action.append('Buy')
      if index != len(in_action)-1:
        in_action[index+1] = True

    elif i[0] == True and i[1] == -1:
      proper_action.append('Sell')
      if index != len(in_action)-1:
        in_action[index+1] = False

    else :
      proper_action.append('no action')
      if index != len(in_action)-1:
        in_action[index+1] = in_action[index]
  return proper_action

history['action'] = set_action(history['in_action'],history['is_proper_4_action'])

with open('log.txt', 'w') as f:
  for index, row in history.iterrows():
    if row['action'] == 'Sell':
      f.write('time=' +f'{index}'+', action=' +row['action'] +', price='+'{:.3f}'.format(row['Close'])+'\n')
    if row['action'] == 'Buy':
      f.write('time=' +f'{index}'+', action=' +row['action']+', price='+'{:.3f}'.format(row['Close'])+'   ')