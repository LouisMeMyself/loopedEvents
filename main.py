import asyncio
import datetime
import json
import time

import requests


class Constants:
    JOE_EXCHANGE_SG_URL = "https://api.thegraph.com/subgraphs/name/traderjoe-xyz/exchange"


async def genericExchangeQuery(query, sg_url=Constants.JOE_EXCHANGE_SG_URL):
    r = requests.post(sg_url, json={'query': query})
    assert (r.status_code == 200)
    return json.loads(r.text)


async def reloadAssets(min_avax_liq):
    skip, queryExchange, tempdic = 0, {}, {}
    while skip == 0 or len(queryExchange["data"]["tokens"]) == 1000:
        queryExchange = await genericExchangeQuery(
            "{tokens(first: 1000, skip: " + str(skip) + "){id, symbol, liquidity, derivedAVAX}}")
        for tokens in queryExchange["data"]["tokens"]:
            liq = float(tokens["liquidity"]) * float(tokens["derivedAVAX"])
            if liq >= min_avax_liq:
                symbol = tokens["symbol"].lower().replace(" ", "")
                if symbol in tempdic:
                    if tempdic[symbol]["liq"] < liq:
                        tempdic[symbol] = {"id": tokens["id"], "liq": liq}
                else:
                    tempdic[symbol] = {"id": tokens["id"], "liq": liq}
        skip += 1000

    name2address = {}
    for key, value in tempdic.items():
        if key[0] == "w" and key[-2:] == ".e":
            name2address[key[1:-2]] = value["id"]
        elif key[-2:] == ".e":
            name2address[key[:-2]] = value["id"]
        elif key in name2address:
            pass
        else:
            name2address[key] = value["id"]

    with open("tokenList.json", "w") as f:
        json.dump(name2address, f)
    print("reloaded, found {} tokens ({})".format(len(name2address),
                                                  datetime.datetime.utcnow().strftime("%D:%M:%Y - %H:%M:%S")))


async def doStuff():
    t = 0
    while 1:
        if time.time() - t > 3600:
            await reloadAssets(100)


        t = time.time()
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(doStuff())

