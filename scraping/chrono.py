from typing import List
from bs4 import BeautifulSoup
from base_scraper import BaseScraper
import schedule
import time

class Chrono24Scraper(BaseScraper):
    """
    A web scraper for extracting watch names and prices from Chrono24.
    Attributes:
    ----------
    User_Agent : str
        User agent string for making requests.
    """
    User_Agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    )

    def __init__(self) -> None:
        """
        Initializes the LuxuryWatchesScraper class.
        Parameters:
        ----------
        None
        """
        super().__init__()

    def extract_data(cls, response):
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract titles as before
        titles = soup.find_all(
            "div", class_="text-sm text-sm-md text-bold text-ellipsis"
        )

        # Attempt to find all 'text-bold' elements
        all_bold_elements = soup.find_all("div", class_="text-bold")

        # Filter out those 'text-bold' elements that contain a 'span' with class 'currency'
        prices = [
            elem for elem in all_bold_elements if elem.find("span", class_="currency")
        ]

        # Assuming your logic for marks remains unchanged
        marks = soup.find_all("div", class_="text-sm text-sm-md text-ellipsis m-b-2")

        return titles, prices, marks

def job():
    """
    The job to run periodically.
    """
    scraper = Chrono24Scraper()
    base_url = (
        "https://www.chrono24.com/rolex/submariner--mod1-{}.htm?query=Rolex+Submariner"
    )

    scraper.scrape_all_pages(base_url)
    scraper.save_to_csv(filename="chrono.csv", include_mark=True)
    print("Scraper run complete.")

if __name__ == "__main__":
    job()  # Run job immediately when script starts.
    # Schedule the job every 10 minutes
    schedule.every(10).minutes.do(job)

    print("Scheduler started.")
    # Keep running in a loop.
    while True:
        schedule.run_pending()
        time.sleep(1)