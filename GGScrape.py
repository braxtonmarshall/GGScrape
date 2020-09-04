import requests
import os
from bs4 import BeautifulSoup
import concurrent.futures
MAX_THREADS = 5

class GGScraper (object):
    """ This class is a webscraper for the op.gg website that aims to collect summoner names
    ranks, and total games played for match data collection.
    """

    def __init__(self, BaseURL, fileOut, region, baseRank):
        """ GGScraper Constructor"""

        self.BaseURL = BaseURL
        self.file = fileOut
        self.region = region
        self.baseRank = ''.join(
            [i for i in baseRank if not i.isnumeric()]).rstrip().lower()
        self.rank_array = ["challenger", "grandmaster", "master",
                           "diamond", "platinum", "gold", "silver", "bronze", "iron"]
        try:
            self.target_index = self.rank_array.index(self.baseRank) + 1
        except ValueError:
            self.target_index = 3
            print("Rank is not valid. Stopping after Master.")
        self.bad_rank_int = 0
        self.page_tracker = 1
        self.findSummoners()

    def process_futures(self, fs, exe):
        """ Clear futures_done set to allow executor to continue grabbing html from urls """
        for future in fs:
            html = future.result()
            if self.bad_rank_int > 600:
                exe.shutdown(wait=False)
                return
            dict_to_write = self.parse_html(html, self.page_tracker)
            if type(dict_to_write) is dict:
                self.write_to_file(dict_to_write)
                del dict_to_write
                self.page_tracker += 1
        fs.clear()

    def findSummoners(self):
        """ Find all summoners on Op.gg """

        threads = MAX_THREADS
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as exe:
            # enforcing an upper-bound limit on threads to keep memory usage low using sets of future sequences
            futures_done = set()
            futures_notdone = set()
            urls = self.generate_urls()
            for url in urls:
                try:
                    futures_notdone.add(exe.submit(self.download_html, url))
                # sending exe.shutdown(wait=false) to exit early generates a run-time error
                except RuntimeError:
                    return
                if len(futures_notdone) >= MAX_THREADS:

                    done, futures_notdone = concurrent.futures.wait(
                        futures_notdone, return_when=concurrent.futures.FIRST_COMPLETED)
                    futures_done.update(done)
                    self.process_futures(futures_done, exe)

    def download_html(self, url):
        """ Download HTML from a URL and return"""

        currPage = requests.get(url)
        html = BeautifulSoup(currPage.text, 'lxml')
        return html

    def generate_urls(self):
        """ Generate and return a list of URLs"""

        urls = list()
        for i in range(1, 3000):
            urls.append(self.BaseURL + "page={}".format(i))
        return urls

    def parse_html(self, html, pagenum):
        """ Parse HTML for summoner name and rank and return a dictionary"""

        print("[+] Parsing Page Number " +
              str(pagenum) + "\tRegion: " + self.region)
        summoner_dict = {}
        results = html.find_all("tr", attrs={"class": "ranking-table__row"})
        for result in results:
            try:
                SummonerName = result.find(
                    "td", attrs={"class": "select_summoner ranking-table__cell ranking-table__cell--summoner"}).select_one("span").text
                Current_Rank = result.find(
                    "td", attrs={"class": "ranking-table__cell ranking-table__cell--tier"}).text.strip().replace(" ", "")
                Summoner_Wins = result.find(
                    "div", attrs={"class": "winratio-graph__text winratio-graph__text--left"}).text.strip()
                Summoner_Loses = result.find(
                    "div", attrs={"class": "winratio-graph__text winratio-graph__text--right"}).text.strip()
            except AttributeError:
                continue
            Summoner_Total_Games = int(Summoner_Wins) + int(Summoner_Loses)
            # Reached bottom rank, skip summoner
            check_rank = ''.join(
                i for i in Current_Rank if not i.isnumeric()).lower()
            if check_rank not in self.rank_array[:self.target_index]:
                self.bad_rank_int += 1
                pass
            else:
                summoner_dict[SummonerName] = [
                    Current_Rank, str(Summoner_Total_Games)]
        return summoner_dict

    def write_to_file(self, _dict):
        """ Write summoner name and summoner rank from a dictionary to .txt file"""

        # Check if File Exists. If it doesn't, create one
        if not os.path.exists(self.file):
            open(self.file, 'w').close()

        # Write to file only if Summoner does not currently exists already
        with open(self.file, "r+", encoding="utf-8") as file:

            dict_to_write = _dict
            for key in dict_to_write.keys():
                summoner = key
                rank = dict_to_write[key][0]
                games = dict_to_write[key][1]
                full_input = summoner.ljust(
                    16) + "\t\t" + rank + "\t\t" + str(games) + "\n"
                for line in file:
                    if summoner.ljust(16) in line and rank in line:
                        break
                else:
                    file.write(full_input)
                    file.flush()
