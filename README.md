# Merkato Beta v0.1.0

Merkato is a cryptocurrency market making bot used for the purpose of generating cryptocurrency denominated profit.

PROPRIETARY CODE DO NOT TAKE, USE, REPURPUSE, PUBLISH, without written consent of 15chrjef


### Prerequisites

See [requirements.txt](https://github.com/livinginformation/merkato/blob/master/requirements.txt) for the full list of prerequisites.

### Installing

Install all dependencies.

All systems:

For Python2
```
Currently broken, if someone wants to support it, go for it.
```
For Python3
```
 pip3 install -r requirements.txt
```
## Getting Started

Run the following from the top level directory: (Outputs logs to output.log)
```
python3 cli_start.py 2>&1 | tee -a output.log
```

#IMPORTANT FOLLOW THE SETUP INSTRUCTIONS FOR EACH OPTION PROPERTLY, ENTERING INCORRECT DATA WILL LEAD TO PROBLEMS#
From this menu you can
1. Set up your credentials for the exchange (WILL REQUIRE A PASSWORD WHICH SHOULD BE UNIFORM ACROSS ALL EXCHANGES, PASSWORD USED TO ENCRPT KEYS)
2. add a new merkato
3. run current merkatos 
4. manage current merkatos

## Checking Data

run the following from the top level directory:
```
python3 cli_stats.py
```
This will show the data and profitability of each merkato run in a directory
Profit is calculated based only on round trips

## Running the tests

from top level directory:

(not working at the moment)
```
./run_tests.sh
```

## Built With

Python 3, sqlite, tkinter

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us. (TBD)


## Authors

* **Core Contributors**: @evdc, @15chrjef, @livinginformation, @nasaWelder

See also the list of [other contributors](https://github.com/livinginformation/merkato/graphs/contributors) who participated in this project.

## License

PROPRIETARY CODE DO NOT TAKE, USE, REPURPUSE, PUBLISH, without written consent of 15chrjef a bot to track stats across assets on exchanges

