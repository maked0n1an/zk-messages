import sys
from loguru import logger

from utils.constansts import Status
   
def setup_logger_for_output():
    logger.remove()
    logger.add(
        sys.stderr,
        format="<white>{time: MM/DD/YYYY HH:mm:ss}</white> | <level>"
        "{level: <8}</level> | <cyan>"
        "</cyan> <white>{message}</white>",
    )
    logger.add(
        "main.log",
        format="<white>{time: MM/DD/YYYY HH:mm:ss}</white> | <level>"
        "{level: <8}</level> | <cyan>"
        "</cyan> <white>{message}</white>",
    )
    
    logger.level(Status.INFO, no=251, color="<white>")
    logger.level(Status.SUCCESS, no=252, color="<green>")
    logger.level(Status.FAILED, no=253, color="<red>")
    logger.level(Status.ERROR, no=253, color="<red>")
    
    logger.level(Status.RETRY, no=261, color="<yellow>")
    logger.level(Status.DELAY, no=262, color="<yellow>")

    return logger

loggers = {}

def setup_logger_for_wallet(wallet_number):
    if wallet_number not in loggers:
        wallet_logger = logger.bind(wallet_name=wallet_number)       
        wallet_logger.add(
            rf"logs\log_{wallet_number}.log",
            format="<white>{time: MM/DD/YYYY HH:mm:ss}</white> | <level>"
            "{level: <8}</level> | <cyan>"
            "</cyan> <white>{message}</white>",
            filter=lambda record: record["extra"].get("wallet_name") == wallet_number
        )        
        loggers[wallet_number] = wallet_logger
        return wallet_logger
    else:
        return loggers[wallet_number]
     