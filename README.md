Prerequisites before starting the app

(1) Bitcoin core must be installed globally
(2) btcdeb - https://github.com/bitcoin-core/btcdeb.git must be installed globally
    - run ./configure with  --enable-dangerous flag
(3) clone https://github.com/anshika1307-code/ord-btclock
    - run cargo build --release in the above directory
    - run ord env
    - go to env/batch.yaml , change rune name to UNCOMMONGOODS, supply to 10000, cap to 9
    - go to env/bitcoin.conf add fallbackfee=0.0001
(4) change the ORD_DIRECTORY in app.py,liquidator.py,pathOneUnclock.py, pathTwoUnlock.py  accordingly.do the same in indexer.py correspondingly.
(5) launch the app.py
(6) 