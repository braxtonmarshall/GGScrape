import GGScrape
import os
from collections import OrderedDict

class MainDriver(object):

    def __init__(self):

        self.files = list()
        self.Regions_opgg = ["na", "kr", "euw", "oce", "eune", "lan"]

    def run(self):
        
        baseRank = input("Enter lowest acceptable rank: ")
        for region in self.Regions_opgg:
            if region == "kr":
                BaseURL = 'https://www.op.gg/ranking/ladder/'
            else:
                BaseURL = 'https://{}.op.gg/ranking/ladder/'.format(region)
            
            file = "{}_summoners.txt".format(region)
            self.files.append(file)

            # Instantiate a new GGScraper and run
            print("Parsing Region: " + region)
            Scraper = GGScrape.GGScraper(BaseURL, file, region, baseRank)
            Scraper.runCrawler()


    def sort_summoner_file(self):

        tmp_file = "tmp.txt"
        for file in self.files:
            print("[+] Sorting " + file)
            with open(file, 'r', encoding="utf-8") as fi, \
                open(tmp_file, 'w', encoding="utf-8") as fo:
                lines = (line.rstrip() for line in fi)
                unique_lines = OrderedDict.fromkeys( (line for line in lines if line ))
                for key in unique_lines.keys():
                    fo.write(key + "\n")
            os.remove(file)
            os.rename(tmp_file, file)



if __name__ == '__main__':

    Scraper = MainDriver()
    Scraper.run()
    Scraper.sort_summoner_file()
