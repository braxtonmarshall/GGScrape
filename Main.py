import GGScrape
import os
from collections import OrderedDict

class MainDriver(object):

    def __init__(self):

        self.files = list()
        self.Regions_opgg = ["na", "kr", "euw", "oce", "eune", "lan"]
        self.file = ""

    def sort_summoner_file(self):

        tmp_file = "tmp.txt"
        for file in self.files:
            print("[+] Sorting " + file)
            with open(file, 'r', encoding="utf-8") as fi, \
                    open(tmp_file, 'w', encoding="utf-8") as fo:
                lines = (line.rstrip() for line in fi)
                unique_lines = OrderedDict.fromkeys(
                    (line for line in lines if line))
                for key in unique_lines.keys():
                    fo.write(key + "\n")
            os.remove(file)
            os.rename(tmp_file, file)


if __name__ == '__main__':

    Draftsmart = MainDriver()

    baseRank = input("Enter lowest acceptable rank: ")
    baseRegion = input("Enter region: ")
    if baseRegion == "kr":
        BaseURL = 'https://www.op.gg/ranking/ladder/'
    else:
        BaseURL = 'https://{}.op.gg/ranking/ladder/'.format(baseRegion)

    Draftsmart.file = "{}_summoners.txt".format(baseRegion)

    # Instantiate a new GGScraper and run
    print("Parsing Region: " + baseRegion)
    Scraper = GGScrape.GGScraper(
        BaseURL, Draftsmart.file, baseRegion, baseRank)

    # Clean up duplicates in file
    Draftsmart.sort_summoner_file()
