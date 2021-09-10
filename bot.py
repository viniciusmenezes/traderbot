import websocket, json, pprint, talib, numpy, config
from binance.client import Client
from binance.enums import *

client = Client(config.API_KEY, config.API_SECRET, tld='com')

SOCKET = "wss://stream.binance.com:9443/ws/btcusdt@kline_1m"
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_SYMBOL = 'BTCUSDT'
TRADE_QUANTITY = 0.0001

closes = []
in_position = False
close_orderbuy = 0

def on_open(ws):
    print('opened connection')

def on_close(ws):
    print('closed connection')

def order(quantity, symbol, side, order_type=ORDER_TYPE_MARKET):
    try:
        print("sending order")
        order = client.create_order(
            symbol=symbol,
            side=side,
            type=order_type,
            quantity=quantity
        )
        print("order info")
        print(order)
    except Exception as e:
        print("there was a problem ordering - {}".format(e))
        return False    
    return True


def on_message(ws, message):
    global closes

    print('received message')
    json_message = json.loads(message)
    # print(json_message)
    pprint.pprint(json_message)

    candle = json_message['k']
    is_candle_closed = candle['x']
    close = candle['c']
    close_time = candle['T'] #Kline close time

    if is_candle_closed:
        print("candle closed at {}".format(close))
        closes.append(float(close))
        print("closes")
        print(closes)

        #Calcula RSI
        if len(closes) > RSI_PERIOD:
            np_closes = numpy.array(closes)
            rsi = talib.RSI(np_closes, RSI_PERIOD)
            print("all RSIs calculated so far")
            print(rsi)
            last_rsi = rsi[-1]
            print("the current RSI is {}".format(last_rsi))

            #calcular percentual de valorização e verificar se o valor do Close é maior do que o valor 
            # if last_rsi > RSI_OVERBOUGHT and in_position:
            if in_position and closes[-1] > ((close_orderbuy * 0.01) + close_orderbuy):
                print("Overbought! SELL SELL SELL!")
                #vender a quantidade de foi comprada
                order_succeeded = order(TRADE_QUANTITY, TRADE_SYMBOL, SIDE_SELL)
                if order_succeeded:
                    in_position = False

            if last_rsi < RSI_OVERSOLD and not in_position:
                if in_position:
                    print("It is oversolv, but you already own it. Nothing to do.")
                else:
                    #Verificar saldo na conta antes de comprar
                    print("Oversold! BUY BUY BUY!")                    
                    close_orderbuy = closes[-1]
                    #calcular a quantidade de moeda a partir de 15 dolares
                    # quantity = (15/close_orderbuy)
                    # order_succeeded = order(quantity, TRADE_SYMBOL, SIDE_BUY)
                    order_succeeded = order(TRADE_QUANTITY, TRADE_SYMBOL, SIDE_BUY)
                    if order_succeeded:
                        in_position = True
                        
                

ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)    
ws.run_forever()