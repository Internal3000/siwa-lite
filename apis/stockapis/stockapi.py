

class StockAPI:
    '''
    Class to interact with stock data API
    '''
    TIMEOUT = 60
    def __init__(self, url: str, source: str) -> None:
        """
        Constructs all the necessary attributes for the StockAPI object.

        Parameters:
            url (str): URL of the API.
            source (str): Source of the data.
        """
        self.url = url
        self.source = source
