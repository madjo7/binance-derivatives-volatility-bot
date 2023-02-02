Derivatives Volatility Skimmer Bot for Binance
==============================

What Is This?
-------------
This is a simple Python bot used to "skim" returns by setting up either long or short positions in combination with an opposite (and equal) take-profit (TP) position. High leverage allows us to set low profit requirements resulting in quick TP execution since markets are extremely volatile even when volume is low. Every TP and position pair executed results in net profit by default. <br>

Should I use this to trade?
-------------
No. This is an unfinished weekend project and is not meant to be used by anyone on the live Binance net. The bot is incomplete and the trading logic has flaws and may result in margin calls and significant losses.<br>
Please only use this in the available testing environment:<br><br>
[testnet](https://testnet.binancefuture.com/en/futures/BTCUSDT)<br><br>
As a note: an updated instance of this bot currently runs on my Raspberry Pi server. Testnet and live trading have been successful and profitable but only in combination with manual intervention. Losses have occurred.

How To Use This
---------------
Open project with editor of choice. <br>
Run the following pip command in terminal:<br>
```
pip install -r requirements.txt
```
When familiar with the code you can run the following Python command in terminal to start an instance of the bot:<br>
```
python bot.py
```