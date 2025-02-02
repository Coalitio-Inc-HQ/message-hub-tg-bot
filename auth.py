from fastapi import FastAPI, Depends, Request, HTTPException
from core.config import API_KEY
from logger.log_config import logger
import datetime

async def verify_api_key(request: Request):
    if API_KEY:
        key = request.headers.get("API-KEY")
        if key:
            if key == API_KEY:
                return key
            else:
                logger.info(f"Нверный API_KEY {key}.")
                raise HTTPException(422)
        else:
            raise HTTPException(422)
    else:
        return "Test mode"