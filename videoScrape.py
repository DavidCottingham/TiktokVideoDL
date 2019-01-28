from selenium import webdriver
from bs4 import BeautifulSoup
from contextlib import closing
import requests
import argparse
import time
import datetime
import os
import csv

def setUpArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory",
                        help="(Parent) Directory path to download to")
    parser.add_argument("-u", "--url",
                        help="Single URL to scrape video from")
    parser.add_argument("-f", "--file", nargs="?", const="list.txt", default=None,
                        help="Specify a .txt file with a list of URLs to scrape")
    args = parser.parse_args()
    return args

def makeDir(dirName):
    homePath = os.path.expanduser("~")
    vidFolder = "Videos"
    tiktokFolder = "TikTok"

    directory = os.path.join(homePath, vidFolder + os.path.sep + tiktokFolder)

    if dirName:
        if os.path.isdir(dirName):
            directory = dirName
        else:
            print("Provided path", dirName, "does not exist")

    try:
        os.makedirs(directory, exist_ok=True)
        return directory
    except OSError as e:
        print("Directory error")
        raise e
        return None

def downloadVideo(url, userID, videoID, dirName):
    #Make video filename
    #omit "@" on userID
    fname = userID[1:] + " - " + videoID + ".mp4"
    filePath = os.path.join(dirName, fname)

    if os.path.exists(filePath):
        print("File", fname, "already exists. Skipping download")
        return False

    #Download video file
    try:
        # with closing to ensure stream connection always closed
        with closing(requests.get(url, stream=True)) as r:
            if r.status_code == requests.codes.ok:
                # "wb" = open for write and as binary file
                with open(filePath, "wb") as mediaFile:
                    for chunk in r:
                        mediaFile.write(chunk)
                #print("Video get!")
                return True
            else:
                # if media file could not be opened, report status code to user
                print("Could not get video. Status code", r.status_code, "on video", url)
                return False
    except requests.exceptions.ConnectionError:
        # if lost connection, report status code to user
        print("Connection error! Status code", r.status_code, "on video", url)
        return False

def getURLsFromFile(filePath):
    print("Getting URLs from", filePath)
    urls = []
    try:
        with open(filePath, "r") as listFile:
            for t in listFile:
                urls.append(t.strip())
            return urls
    except FileNotFoundError:
        print(filePath, "file not found!")
        return []
    except Exception as e:
        raise e

def checkCSVFile(filePath, headers):
    try:
        #Check if metadata file exists. If not, check if headers exist
        if not os.path.isfile(filePath):
            if not headers:
                return False

            # create metadata file with headers
            with open(filePath, "w") as csvfile:
                csvwriter = csv.DictWriter(csvfile, headers)
                csvwriter.writeheader()
        return True
    except Exception as e:
        raise e

def writeMetadata(filePath, headers, metadata):
    try:
        if checkCSVFile(filePath, headers):
            with open(filePath, "a") as csvfile:
                csvwriter = csv.DictWriter(csvfile, headers)
                csvwriter.writerow(metadata)
        else:
            print("could not make metadata file")
    except FileNotFoundError:
        print(filePath, "file not found!")
        return
    except Exception as e:
        raise e

def debugMetadataCheck(filePath):
    with open(filePath, "r") as csvfile:
        csvreader = csv.DictReader(csvfile)
        headers = csvreader.fieldnames
        print(headers)
        for row in csvreader:
            for k, v in row.items():
                print(k, v, sep=": ")

def main():
    args = setUpArgs()
    urls = []
    CSV_HEADERS = ["videoID", "videoURL", "pageURL", "userName", "userID",
                    "userURL", "sound", "caption", "timeAcquired"]
    CSV_FILENAME = "__metadata.csv"

    if args.directory:
        directory = makeDir(args.directory)
    else:
        directory = makeDir("")
    if not directory:
        return

    if args.file:
        urls = getURLsFromFile(args.file)
    elif args.url:
        urls.append(args.url)
    else:
        inputURL = input("TikTok page: ")
        if inputURL:
            urls.append(inputURL)
        else:
            print ("No URL entered.")
            return

    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    #options.add_argument('window-size=1920x1080')
    chrome = webdriver.Chrome(chrome_options=options)

    for url in urls:
        metadata = {}
        print("Scraping video from", url)
        try:
            chrome.get(url)
            time.sleep(1)

            #page URL metadata
            pageURL = chrome.current_url.split("?")[0]
            metadata["pageURL"] = pageURL
        except selenium.common.exceptions.WebDriverException:
            print("Chrome error: WebDriverException")
            return
        except Exception as e:
            raise e

        page = BeautifulSoup(chrome.page_source, "html.parser")
        player_div = page.find("div", id = "Video")

        #video ID metadata
        videoID = player_div.get("ga_label")
        metadata["videoID"] = videoID

        try:
            #video URL metadata
            videoURL = player_div.video.get("src")
            metadata["videoURL"] = videoURL
        except AttributeError:
            print("Video not found")
            continue

        metadata_div = page.find("div", id = "metadata")

        #user name metadata
        userName = metadata_div.contents[0].h1.text
        metadata["userName"] = userName

        #user ID metadata
        userID = metadata_div.contents[1].p.text
        metadata["userID"] = userID

        #user profile URL metadata
        userURL = metadata_div.contents[0].get("href")
        metadata["userURL"] = userURL

        #sound metadata
        ps = metadata_div.find_all("p")
        sound = ps[1].text
        metadata["sound"] = sound

        #caption metadata
        caption = page.find("p", id = "caption").text
        metadata["caption"] = caption

        #timestamp metadata
        timestamp = readable = datetime.datetime.fromtimestamp(time.time()).isoformat()
        metadata["timeAcquired"] = timestamp

        if downloadVideo(videoURL, userID, videoID, directory):
            writeMetadata(os.path.join(directory, CSV_FILENAME), CSV_HEADERS, metadata)
            #debugMetadataCheck(os.path.join(directory, CSV_FILENAME))

if __name__ == "__main__":
    main()
