#!/usr/bin/env python3

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
from contextlib import closing
from enum import Enum
import requests
import argparse
import time
import datetime
import os
import csv

#New URL type: https://www.tiktok.com/share/video/6642696300275961093
    #Can convert all to these to get new info? (likes, comments, music URL, use URL)

class LoggingLevel(Enum):
    noLog = 0
    moderate = 1
    verbose = 2

#Define CLI arguments using argparse
def setUpArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory",
                        help="(Parent) Directory to download videos to")
    parser.add_argument("-u", "--url",
                        help="Single URL to scrape video from")
    parser.add_argument("-f", "--file", nargs="?", const="list.txt", default=None,
                        help="Specify a .txt file with a list of URLs to scrape")
    args = parser.parse_args()
    return args

#Create default download directory at ~/Videos/TikTok if does not exists
#User-specified directory is checked for but not created
def makeDir(dirName):
    #default download location
    homePath = os.path.expanduser("~")
    vidFolder = "Videos"
    tiktokFolder = "TikTok"

    #join above folders to path
    directory = os.path.join(homePath, vidFolder + os.path.sep + tiktokFolder)

    #check if user-specified path exists
    if dirName:
        if os.path.isdir(dirName):
            directory = dirName
        else:
            print("Provided path", dirName, "does not exist")

    #make default directory if doesn't exist
    try:
        os.makedirs(directory, exist_ok=True)
        return directory
    except OSError as e:
        print("Directory error")
        raise e
        return None

#Download the video from the page to the directory
def downloadVideo(url, userID, videoID, dirName):
    #Make video filename using user ID and video ID
    fname = userID + " - " + videoID + ".mp4"
    filePath = os.path.join(dirName, fname)

    #Check if a video with the same filename exists. Since we are using the
        #video ID in the filename, we can assume it will be the same video
        #If it exists, skip it. We don't want to download the same video again
        #Return False so metadata doesn't get saved again either
    if os.path.exists(filePath):
        print("File", fname, "already exists. Skipping download")
        return False

    #Try to download video file
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

#Pull list of URLs from user file so they can all be downloaded
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

#Check if metadata file exists. Create if doesn't yet
def checkCSVFile(filePath, headers):
    try:
        #Check if metadata file exists. If not, check if headers exist
        if not os.path.isfile(filePath):
            if not headers:
                #If headers not provided, can not create metadata file, so cancel
                return False

            # create metadata file with headers
            with open(filePath, "w") as csvfile:
                csvwriter = csv.DictWriter(csvfile, headers)
                csvwriter.writeheader()
        return True
    except Exception as e:
        raise e
        return False

#Write video metadata line to file
def writeMetadata(filePath, headers, metadata):
    try:
        if checkCSVFile(filePath, headers):
            #Open with append to add new metadata to end of file
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

#Print out metadata file in format "Header: Data"
def debugMetadataCheck(filePath):
    with open(filePath, "r") as csvfile:
        csvreader = csv.DictReader(csvfile)
        headers = csvreader.fieldnames
        print(headers)
        for row in csvreader:
            for k, v in row.items():
                print(k, v, sep=": ")

def getUserPage():
    pass

def getSoundPage():
    pass

def main():
    captureVidMeta = True
    captureMusicMeta = True
    captureUserMeta = True

    #define and get CLI args first
    args = setUpArgs()
    urls = []
    #Metadata headers
    CSV_HEADERS = ["videoID", "videoURL", "pageURL", "userName", "userID",
                    "userURL", "sound", "caption", "timeAcquired"]
    CSV_FILENAME = "__metadata.csv"

    #check if user has provided download directory.
        #Create the default directory if needed
    if args.directory:
        directory = makeDir(args.directory)
    else:
        directory = makeDir("")
    if not directory:
        return

    #Check if user has provided list of URLs or single URL or no URL
    if args.file:       #list of urls provided via CLI args
        urls = getURLsFromFile(args.file)
    elif args.url:      #single url provided via CLI args
        urls.append(args.url)
    else:               #if nothing provided via CLI args, ask for user input
        inputURL = input("TikTok page: ")
        if inputURL:
            urls.append(inputURL)
        else:
            #If user didn't provide URL, abort
            print ("No URL entered.")
            return

    #Set up Chrome options to run headless then start Chrome webdriver with options
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    #options.add_argument('window-size=1920x1080')
    chrome = webdriver.Chrome(chrome_options=options)

    #start scraping each provided URL
    for url in urls:
        metadata = {}
        print("Scraping video from", url)
        try:
            chrome.get(url)
            #Waiting for javascript to load video
                #If don't wait, video URL will be empty
            time.sleep(1)

            #page URL metadata
            pageURL = chrome.current_url.split("?")[0]
            #print(pageURL)
            if "/share/video/" in pageURL:
                #print("Share type")
                pass
            else:
                #make share type
                print("not share type")
                tempID = pageURL.split("/")[-1].split(".")[0]
                metadata["videoID"] = tempID
                pageURL = "https://www.tiktok.com/share/video/" + tempID
                chrome.get(pageURL)
                #Waiting for javascript to load video
                    #If don't wait, video URL will be empty
                time.sleep(1)
            #metadata["pageURL"] = pageURL
        except WebDriverException as e:
            print("Chrome error: WebDriverException")
            #raise e
            return
        except Exception as e:
            raise e
            return

        #Pass the page source to BeautifulSoup for easier parsing
        page = BeautifulSoup(chrome.page_source, "html.parser")

        #video ID metadata
        videoID = pageURL.split("/")[-1]
        metadata["videoID"] = videoID

        #video URL metadata
        try:
            videoURL = "https://tiktok.com" + page.find("video", class_ = "_video_card_").get("src")
            #metadata["videoURL"] = videoURL
        except AttributeError:
            #Lazy way of checking if user provided bad URL or video was deleted
                #page will not have video to load (no src in video div) if no video
            print("Video not found. Check your URL or video was removed")
            #continue to next provided URL if video not found
            continue

        #user name metadata
        userName = page.find("p", class_ = "_video_card_big_user_info_nickname").text
        metadata["userName"] = userName

        #user ID metadata
        userID = page.find("p", class_ = "_video_card_big_user_info_handle").text[1:]
        #print(userID)
        metadata["userID"] = userID

        #user profile URL metadata
        userURL = page.find("a", class_ = "_video_card_big_user_info_").get("href")
        metadata["userURL"] = userURL

        #user number
        userNum = userURL.split("/")[-1]
        #print(userNum)
        #metadata["userNum"] = userNum

        #sound metadata
        sound = page.find("div", class_ = "_video_card_big_meta_info_music").a.text
        metadata["sound"] = sound

        #sound share URL metadata
        soundURL = page.find("div", class_ = "_video_card_big_meta_info_music").a.get("href")
        #metadata["soundURL"] = soundURL

        #sound number metadata
        soundNum = soundURL.split("/")[-1]
        #print(soundNum)
        #metadata["soundNum"] = soundNum

        #caption metadata
        caption = page.find("h1", class_ = "_video_card_big_meta_info_title").span.text
        metadata["caption"] = caption

        #counts metadata_div
        counts = page.find("div", class_ = "_video_card_big_meta_info_count").text
        #metadata["counts"] = counts

        #timestamp metadata
        timestamp = readable = datetime.datetime.fromtimestamp(time.time()).isoformat()
        metadata["timeAcquired"] = timestamp

        #get video from URL scraped. send userID, videoID and DL directory
        if downloadVideo(videoURL, userID, videoID, directory):
            #only if video downloaded successfully write metadata to file
            writeMetadata(os.path.join(directory, CSV_FILENAME), CSV_HEADERS, metadata)
            #debugMetadataCheck(os.path.join(directory, CSV_FILENAME))

    #Close Chrome properly
    chrome.quit()

if __name__ == "__main__":
    main()
