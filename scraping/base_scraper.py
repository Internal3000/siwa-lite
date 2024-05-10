import logging
from typing import List
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import pandas as pd
import time
import os
from datetime import datetime


class BaseScraper:
    """
    A base class for web scrapers.

    Attributes:
    ----------
    headers : dict
        Headers to be used in HTTP requests.
    data : List[str]
        List to store scraped data.
    """

    def __init__(self) -> None:
        """
        Initializes the BaseScraper class.

        Parameters:
        ----------
        None
        """
        self.headers: dict = {"User-Agent": self.User_Agent}
        self.data: List[str] = []
        logging.basicConfig(level=logging.INFO)
        retry_strategy = Retry(total=3, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.http = requests.Session()
        self.http.mount("https://", adapter)
        self.http.mount("http://", adapter)

    def scrape_names_from_page(cls, url) -> None:
        """
        Scrapes data from a single page.

        Parameters:
        ----------
        url : str
            The URL of the page to scrape.
        Returns:
        -------
        None
        """
        response = cls.http.get(url, headers=cls.headers)
        base_url = "https://www.chrono24.com"
        if response.status_code == 200:
            titles, prices, marks = cls.extract_data(
                response
            )  # Unpack the returned tuple

            min_length = min(len(titles), len(prices), len(marks))

            for i in range(min_length):
                title = titles[i].text.strip() if titles else None
                price = prices[i].text.strip() if prices else None
                mark = marks[i].text.strip() if marks else None
                # href = tags[i].get("href")
                # full_url = base_url + href
                cls.data.append(
                    {
                        "Watch_Name": title,
                        "Price": price,
                        "Watch_Mark": mark,
                    }
                )
                logging.info(
                    f"Name: {title}, Price: {price}, Mark: {mark}"
                )

        else:
            logging.error(
                "Failed to retrieve the webpage. Status code: %d", response.status_code
            )

        time.sleep(10)

    def scrape_all_pages(
        self, base_url: str, start_page: int = 1, num_pages: int = 6
    ) -> None:
        """
        Scrapes data from multiple pages.

        Parameters:
        ----------
        base_url : str
            The base URL of the website to scrape.
        start_page : int, optional
            The starting page number. Default is 1.
        num_pages : int, optional
            The number of pages to scrape. Default is 5.

        Returns:
        -------
        None
        """
        page_number = start_page
        while page_number <= 156:
            url = base_url.format(page_number)
            try:
                response = self.http.get(url, headers=self.headers, verify=False)
                if response.status_code == 200:
                    logging.info(f"Scraping page {page_number}")
                    self.scrape_names_from_page(url)
                    page_number += 1
                    time.sleep(5)
                else:
                    logging.error(
                        "Failed to retrieve the webpage. Status code: %d",
                        response.status_code,
                    )
                    break
            except requests.exceptions.RequestException as e:
                logging.error("An error occurred while making the request: %s", e)
                break

    def save_to_csv(self, filename: str, include_mark: bool = True) -> None:
        """
        Updated to append data to CSV if file exists, else create new.
        """
        if not self.data:
            logging.error("No data to save.")
            return

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for row in self.data:
                    row["Datetime"] = now

        columns = ["Watch_Name", "Price", "Datetime"]
        if include_mark:
            columns.append("Watch_Mark")

        df = pd.DataFrame(self.data, columns=columns)

        if os.path.exists(filename):
            df.to_csv(filename, mode="a", header=False, index=False)
        else:
            df.to_csv(filename, index=False)

        logging.info(f"Data appended to {filename}")

