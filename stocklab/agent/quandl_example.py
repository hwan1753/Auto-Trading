import quandl

quandl.ApiConfig.api_key = 'xy9P1gzEj8QYDWXdoA9P'
data = quandl.get('BCHARTS/BITFLYERUSD',start_date='2019-03-08',end_date='2019-03-08')

print(data)