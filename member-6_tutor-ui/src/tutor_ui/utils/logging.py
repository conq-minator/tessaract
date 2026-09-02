import logging
import sys

def setup_logging(log_level: str) -> None:
    """Setup structured logging for the application."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Basic config for now, can be expanded to JSON structured logging later
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    
    # Reduce noise from external libraries
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
