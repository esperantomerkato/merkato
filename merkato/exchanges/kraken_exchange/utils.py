import krakenex

import logging
root_log = logging.getLogger("myapp")
log = root_log.getChild(__name__)

def validate_kraken(config):
    public_key = config["public_api_key"]
    private_key = config["private_api_key"]
    client = krakenex.API(public_key, private_key)

    try:
        client.query_private('OpenOrders', {'oflags': 'viqc'})
    except Exception as e:
        log.error(e)
        return False

    return True