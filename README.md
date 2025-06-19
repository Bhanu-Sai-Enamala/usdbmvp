# USDB MVP

## Prerequisites Before Starting the App

To run this app, ensure the following dependencies and setups are completed:

---

### 1. Install Bitcoin Core

Bitcoin Core must be installed **globally** and added to your system's PATH.

---

### 2. Install `btcdeb` with Dangerous Flag

Clone the official Bitcoin Script Debugger:
while installing, run the ./configure with the follwoing flag below.

```bash
git clone https://github.com/bitcoin-core/btcdeb.git

./configure --enable-dangerous

```

---

### 3. Clone and Build `ord-btclock`

```bash
git clone https://github.com/anshika1307-code/ord-btclock
```
sync to branch named "bhanu" 
Then build 
``` bash
cargo build --release
```

#### Additional Setup for `ord-btclock`:

- Run the environment setup:
  
  ```bash
  ord env
  ```

- Edit `env/batch.yaml`:
  - Set `rune` name to `UNCOMMONGOODS`
  - Set `supply` to `10000`
  - Set `cap` to `9`

- Edit `env/bitcoin.conf`:
  - Add the following line:

    ```
    fallbackfee=0.0001
    ```

---

### 4. Update Directory Paths in Python Files

Update the `ORD_DIRECTORY` variable in the following files to match your cloned `ord-btclock` path:

- `app.py`
- `liquidator.py`
- `pathOneUnclock.py`
- `pathTwoUnlock.py`
- `indexer.py`

Make sure all paths point to your correct local `ord-btclock` directory.