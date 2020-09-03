import requests
import os
import codecs
import time
from bs4 import BeautifulSoup
from multiprocessing import Queue, Manager, Pool, cpu_count

class GGScraper (object):
    """ This class is a webscraper for the op.gg website that aims to collect summoner names
    and summoners ranks for match data collection.
    """

    def __init__ (self, BaseURL, fileOut, region, baseRank):
        """ GGScraper Constructor"""

        self.BaseURL = BaseURL
        self.fileOut = fileOut
        self.region = region
        self.baseRank = ''.join([i for i in baseRank if not i.isnumeric()]).rstrip()
        self.rank_array = ["Challenger", "Grandmaster", "Master", "Diamond", "Platinum", "Gold", "Silver", "Bronze", "Iron"]

        try:
            self.target_index = self.rank_array.index(self.baseRank) + 1
        except ValueError:
            self.target_index = 3
            print("Rank is not valid. Stopping after Master.")

        # Multiprocessing Manager for writer Queue
        manager = Manager()
        self.writerQueue = manager.Queue()
        
    def runCrawler(self):
        """ Run GGCrawler asychronously"""

        # Create Pools
        pool = Pool(cpu_count() + 2)
        jobs = []

        # Start queue for writing to file
        if self.fileOut != None:
            writer = pool.apply_async(self.write_to_file)

        # Create worker jobs
        for i in range(1,10000):
            jobs.append(pool.apply_async(self.findSummoners, ([i])))

        # Wait for jobs to finish
        for job in jobs:
            time.sleep(.5)
            result = job.get()
            if result is True:
                break

        # Clean up, wait for queue to push end message
        if self.fileOut != None:
            self.writerQueue.put("kill")
            writer.get()
        pool.close()
        pool.terminate()
        pool.join()
    
    def findSummoners(self, count):
        """ Find all summoners on Op.gg """

        temp_dict = {}

        url = self.generate_urls(count)
        currPage = self.download_html(url)
        
        print("[+] Parsing Page Number " + str(count) + "\tRegion: " + self.region)
        html = BeautifulSoup(currPage.text, 'lxml')
        temp_dict, bad_rank_count = self.parse_html(html)

        # Send to writer queue
        if type(temp_dict) is dict:
            for key in temp_dict:
                input = key + "/" + temp_dict[key]
                self.writerQueue.put(input)
        # stop processing jobs
        if type(bad_rank_count) is int and bad_rank_count > 10:
            return True
        return False

    def download_html(self, url):
        """ Download HTML from a URL and return"""

        currPage = requests.get(url)
        return currPage

    def generate_urls(self, count):
        """ Generate and return a list of URLs"""

        url = self.BaseURL + "page={}".format(count)
        return url

    def write_to_file(self):
        """ Write summoner name and summoner rank from a dictionary to .txt file"""

        # Check if File Exists. If it doesn't, create one
        if not os.path.exists(self.fileOut):
            open(self.fileOut, 'w').close()
        
        # Write to file only if Summoner does not currently exists already
        with open(self.fileOut, "r+", encoding="utf-8") as file:
            while True:

                input_ = ""
                input_ = self.writerQueue.get()
                
                # If kill message is sent, break while loop
                if input_ == "kill":
                    break

                summoner = input_.split("/")[0]
                rank = input_.split("/")[1]
                full_input = summoner.ljust(16) + "\t\t" + rank + "\n"
                
                for line in file:
                    if summoner.ljust(16) in line and rank in line:
                        break
                else:
                    file.write(full_input)
                    file.flush()

    def parse_html(self, html):
        """ Parse HTML for summoner name and rank and return a dictionary"""

        summoner_dict = {}
        bad_rank_count = 0
        
        results = html.find_all("tr", attrs={"class": "ranking-table__row"})
        for result in results:
            SummonerName = result.find(
                  "td", attrs={"class": "select_summoner ranking-table__cell ranking-table__cell--summoner"}).select_one("span").text
            Current_Rank = result.find(
                   "td", attrs={"class": "ranking-table__cell ranking-table__cell--tier"}).text.strip().replace(" ", "")

            # Reached bottom rank, skip summoner
            #if "Diamond" in Current_Rank or "Platinum" in Current_Rank or "Gold" in Current_Rank or "Silver" in Current_Rank or "Bronze" in Current_Rank:
            check_rank = ''.join(i for i in Current_Rank if not i.isnumeric())
            if check_rank not in self.rank_array[:self.target_index]:
                bad_rank_count += 1
                pass
            else:
                summoner_dict[SummonerName] = Current_Rank
        return summoner_dict, bad_rank_count
