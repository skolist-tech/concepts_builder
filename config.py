import logging

def setup_logging():
    """
    To be imported in main.py and setup logging for the application.
    """
    logging.getLogger().setLevel(logging.INFO)
    file_handler = logging.FileHandler("app.log")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)