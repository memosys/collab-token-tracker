import datetime
from typing import Any, Dict
from fastapi import APIRouter, BackgroundTasks
from discord.enums import (
    InteractionType,
    AppCommandType,
    AppCommandOptionType,
    InteractionResponseType,
)

from ..models.metadata import Metadata
from ..utils.discord import get_option_value
from .message import handle_message
import requests
import json

token_tracker_router = APIRouter(
    prefix="/token-tracker",
    tags=["token-tracker"],
)


@token_tracker_router.get("/metadata")
async def get_token_tracker_metadata() -> Metadata:
    return {
        "manifest": {
            "appId": "token-tracker",
            "developer": "collab.land",
            "name": "tokenTracker",
            "platforms": ["discord"],
            "shortName": "token-tracker",
            "version": {"name": "0.0.1"},
            "website": "https://collab.land",
            "description": "An example Collab.Land action",
        },
        "supportedInteractions": [
            {
                "type": InteractionType.application_command.value,
                "names": ["token-tracker"],
            }
        ],
        "applicationCommands": [
            {
                "metadata": {"name": "tokenTracker", "shortName": "token-tracker"},
                "name": "token-tracker",
                "type": AppCommandType.chat_input.value,
                "description": "/token-tracker",
                "options": [
                    {
                        "name": "token-name",
                        "description": "Name of the person we're greeting",
                        "type": AppCommandOptionType.string.value,
                        "required": True,
                    }
                ],
            }
        ],
    }


@token_tracker_router.post("/interactions")
async def post_token_tracker_interaction(
    req: Dict[str, Any], background_tasks: BackgroundTasks
):
    parsed_req = dict(req)
    token_name = get_option_value(parsed_req, "token-name")


    token_list = requests.get("https://api.coingecko.com/api/v3/coins/list")
    token_mapper = token_list.json()


    token_id = None
    data = None
    for token in token_mapper:
        lower_case_token_name = token_name.lower() if token_name else None

        if lower_case_token_name in (token['id'].lower(), token['symbol'].lower(), token['name'].lower()):
            token_id = token['id']
            break

    if token_id:
        resp = requests.get(f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={token_id}")
        response = resp.json()
        data = parse_response(response)


    else:
        data = 'no data found with {token}'


    callback_url = str(req.get("actionContext").get("callbackUrl"))


    message = f"{data}"
    background_tasks.add_task(handle_message, callback_url, message)
    return {
        "type": InteractionResponseType.channel_message.value,
        "data": {
            "content": message,
            "flags": 1 << 6,
        },
    }


def parse_response(response):
    # Parse JSON if it's a string
    if isinstance(response, str):
        response = json.loads(response)

    if response:
        coin = response[0]
        message = f"**{coin['name']} ({coin['symbol'].upper()})**\n" if 'name' in coin and 'symbol' in coin and coin['name'] is not None and coin['symbol'] is not None else ""
        message += f"**Current price:** ${coin['current_price']:,.2f}\n" if 'current_price' in coin and coin['current_price'] is not None else ""
        message += f"**Market Cap:** ${coin['market_cap']:,.2f}\n" if 'market_cap' in coin and coin['market_cap'] is not None else ""
        message += f"**Market Cap Rank:** {coin['market_cap_rank']}\n" if 'market_cap_rank' in coin and coin['market_cap_rank'] is not None else ""
        message += f"**Fully Diluted Valuation:** ${coin['fully_diluted_valuation']:,.2f}\n" if 'fully_diluted_valuation' in coin and coin['fully_diluted_valuation'] is not None else ""
        message += f"**24h Volume:** ${coin['total_volume']:,.2f}\n" if 'total_volume' in coin and coin['total_volume'] is not None else ""
        message += f"**24h Low/High:** ${coin['low_24h']:,.2f} / ${coin['high_24h']:,.2f}\n" if 'low_24h' in coin and 'high_24h' in coin and coin['low_24h'] is not None and coin['high_24h'] is not None else ""
        message += f"**24h Price Change:** ${coin['price_change_24h']:,.2f}\n" if 'price_change_24h' in coin and coin['price_change_24h'] is not None else ""
        message += f"**24h Market Cap Change:** ${coin['market_cap_change_24h']:,.2f}\n" if 'market_cap_change_24h' in coin and coin['market_cap_change_24h'] is not None else ""
        message += f"**Circulating Supply:** {coin['circulating_supply']:,.2f}\n" if 'circulating_supply' in coin and coin['circulating_supply'] is not None else ""
        message += f"**Total Supply:** {coin['total_supply']:,.2f}\n" if 'total_supply' in coin and coin['total_supply'] is not None else ""
        message += f"**Maximum Supply:** {coin['max_supply']}\n" if 'max_supply' in coin and coin['max_supply'] is not None else ""
        message += f"**All Time High:** ${coin['ath']:,.2f} (Change: {coin['ath_change_percentage']:,.2f}%)\n" if 'ath' in coin and 'ath_change_percentage' in coin and coin['ath'] is not None and coin['ath_change_percentage'] is not None else ""
        message += f"**All Time Low:** ${coin['atl']:,.2f} (Change: {coin['atl_change_percentage']:,.2f}%)\n" if 'atl' in coin and 'atl_change_percentage' in coin and coin['atl'] is not None and coin['atl_change_percentage'] is not None else ""

        if coin['roi'] is not None:
            message += f"**ROI times:** {coin['roi']['times']}\n" if 'times' in coin['roi'] and coin['roi']['times'] is not None else ""
            message += f"**ROI percentage:** {coin['roi']['percentage']}\n" if 'percentage' in coin['roi'] and coin['roi']['percentage'] is not None else ""
            message += f"**ROI currency:** {coin['roi']['currency']}\n" if 'currency' in coin['roi'] and coin['roi']['currency'] is not None else ""

        return message


    else:
        return 'Response is empty.'
