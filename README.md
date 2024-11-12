## How to run the bot?
1. Build the environment: `pip install -r requirements.txt`
2. Create an `.env` file from `.env.example`
3. Run the bot: `python main.py`

## How does QR code scanning work?
1. QR code is updated every 60 seconds (link: https://jakhongir0103.github.io/aipm/).
2. Every QR code expires in 90 seconds ->  user has 30-90 seconds to get to the bot through the QR code.
3. When the user scans the QR code, the current time is stored into the DB.
4. The user can scan a new QR code 60 seconds passed the last one.

## How does encryption work?
1. Encryption: current time in _ms_ -> string
2. Decryption: string -> current time in _ms_

## TODO:
- [ ] improve encryption in the backend
- [ ] deploy the bot on AWS?