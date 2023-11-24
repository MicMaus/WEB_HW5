import aiohttp
import asyncio
from datetime import datetime, timedelta
from json import dumps

# list of currencies to be displayed, could be appended base on user commands:
currencies = ["USD", "EUR"]


# generate list of links based on user input:
async def links_creator():
    links = []
    days_input = days_input_check()
    # asking user whether he wants to see additional currencies
    addit_currencies = input(
        "additional currencies to display (enter the codes separated by coma): "
    ).split(",")
    addit_currencies = [currency.strip().upper() for currency in addit_currencies]
    # check is user requested some additional currencies using index:
    if addit_currencies[0]:
        currencies.extend(addit_currencies)
    print(f"currencies to be displayed: {', '.join(currencies)}")

    for day in range(int(days_input)):
        requested_date = (datetime.today() - timedelta(days=day)).date()
        formatted_requested_date = requested_date.strftime("%d.%m.%Y")
        pb_link = "https://api.privatbank.ua/p24api/exchange_rates?date="
        final_pb_link = pb_link + formatted_requested_date
        links.append(final_pb_link)
    return links


# func used in def links_creator to validate user input for days:
def days_input_check():
    while True:
        days_input = input("Enter the number of days back for currency rates:")
        if days_input and int(days_input) < 11:
            return days_input
        else:
            print("It is mandatory field. Max. days back is 10. Try again")


# collects data from api, with error handling:
async def data_generator(session, link):
    try:
        async with session.get(link) as response:
            print("Status:", response.status)
            if response.status == 200:
                response.raise_for_status()
                content_dict = await response.json()
                formatted_content = await content_formatter(content_dict)
                return formatted_content
            else:
                return f"Error status: {response.status} for date {link[-10:]}"

    except aiohttp.ClientConnectorError as err:
        return f"The following error occurred for date {link[-10:]}: {err}"


# mapping of collected data with required format:
async def content_formatter(content_dict):
    date = content_dict["date"]
    formatted_dict = dict()
    formatted_dict[date] = {}
    print(f"check curren list: {currencies}")
    for cur in currencies:
        for rate_dict in content_dict["exchangeRate"]:
            if rate_dict["currency"] == cur:
                cur_sale = rate_dict["saleRateNB"]
                cur_purchase = rate_dict["purchaseRateNB"]

                if cur not in formatted_dict[date]:
                    formatted_dict[date][cur] = {
                        "sale": cur_sale,
                        "purchase": cur_purchase,
                    }
    # notification in case some of additional currencies do not exist in api:
    for cur in currencies:
        if cur not in formatted_dict[date]:
            print(f"requested currency {cur} does not exist in api for day: {date}")

    return formatted_dict


# main func run separate task for each link(day):
async def main():
    links_list = await links_creator()
    async with aiohttp.ClientSession() as session:
        tasks = [data_generator(session, link) for link in links_list]
        final_dict_list = await asyncio.gather(*tasks)
        print(dumps(final_dict_list, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
