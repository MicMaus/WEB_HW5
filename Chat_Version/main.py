import aiohttp
import asyncio
from datetime import datetime, timedelta
import re


# generate list of links based on user input:
async def links_creator(days_input):
    links = []

    days_input = days_input_check(days_input)
    # limitation max 10 days
    if not days_input:
        return False

    for day in range(int(days_input)):
        requested_date = (datetime.today() - timedelta(days=day)).date()
        formatted_requested_date = requested_date.strftime("%d.%m.%Y")
        pb_link = "https://api.privatbank.ua/p24api/exchange_rates?date="
        final_pb_link = pb_link + formatted_requested_date
        links.append(final_pb_link)
    return links


# func used in def links_creator to validate user input for days:
def days_input_check(days_input):
    if days_input and int(days_input) < 11:
        return days_input
    else:
        return False


# collects data from api, with error handling:
async def data_generator(session, link, currencies):
    try:
        async with session.get(link) as response:
            print("Status:", response.status)
            if response.status == 200:
                response.raise_for_status()
                content_dict = await response.json()
                formatted_content = await content_formatter(content_dict, currencies)
                return formatted_content
            else:
                return f"Error status: {response.status} for date {link[-10:]}"

    except aiohttp.ClientConnectorError as err:
        return f"The following error occurred for date {link[-10:]}: {err}"


# mapping of collected data with required format:


async def content_formatter(content_dict, currencies):
    date = content_dict["date"]
    result = f"{date}:\n "
    print(f"check curren list: {currencies}")
    for cur in currencies:
        for rate_dict in content_dict["exchangeRate"]:
            if rate_dict["currency"] == cur:
                cur_sale = rate_dict["saleRateNB"]
                cur_purchase = rate_dict["purchaseRateNB"]

                result = (
                    result + f"{cur} sale: {cur_sale}, purchase: {cur_purchase};\n "
                )

    # notification in case some of additional currencies do not exist in api:
    cur_not_found = str()
    for cur in currencies:
        if not cur in result:
            cur_not_found = cur_not_found + (
                f"requested currency {cur} does not exist in api for day: {date};\n "
            )
    if cur_not_found:
        result = result + cur_not_found

    return result


async def parser(message):
    currencies = ["USD", "EUR"]
    days_input = "".join(re.findall(r"\d", message))
    pattern = re.compile(r"\b(?!exchange\b)\D+\b")
    additional_currencies = pattern.findall(message)
    additional_currencies = [currency.strip() for currency in additional_currencies]
    additional_currencies = list(filter(None, additional_currencies))
    currencies.extend(additional_currencies)
    links_list = await links_creator(days_input)
    return links_list, currencies


# main func run separate task for each link(day):
async def main(message):
    links_list, currencies = await parser(message)
    if not links_list:
        return "Pls enter days param. Max. days back is 10. Try again"
    async with aiohttp.ClientSession() as session:
        tasks = [data_generator(session, link, currencies) for link in links_list]
        final_result = await asyncio.gather(*tasks)
        return final_result


if __name__ == "__main__":
    asyncio.run(main())
