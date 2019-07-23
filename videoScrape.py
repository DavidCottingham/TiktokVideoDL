#!/usr/bin/env python3

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
from contextlib import closing
import requests
import argparse
import time
import datetime
import os
import csv
import re

#false user-agent to provide to download the video
USERAGENT = "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/44.0.2403.155 Safari/537.36"
DEFAULTSFILENAME = "defaults"
VIDMETAFILENAME = "__videometadata.csv"
USERMETAFILENAME = "__usermetadata.csv"
SOUNDMETAFILENAME = "__soundmetadata.csv"

#empty class to use as a blank argparse namespace
class NM:
    pass

#Define CLI arguments using argparse
def setUpArgs():
    nm = NM()
    defaultsFilepath = os.path.join(os.path.abspath(os.path.dirname(__file__)), DEFAULTSFILENAME)
    defaults = "@" + defaultsFilepath
    parser = argparse.ArgumentParser(fromfile_prefix_chars="@",
                description="If providing a 'defaults' file, arguments must be one per line")
    parser.add_argument("-d", "--directory",
                        help="(Parent) Directory to download videos to")
    parser.add_argument("-u", "--url",
                        help="Single URL to scrape video from")
    parser.add_argument("-f", "--file", nargs="?", const="list.txt", default=None,
                        help="Specify a .txt file with a list of URLs to scrape")
    parser.add_argument("-vm", "--videometadata", action="store_true",
                        help="Flag: Save the video metadata to a CSV file")
    parser.add_argument("-um", "--usermetadata", action="store_true",
                        help="Flag: Save the user / creator metadata to a CSV file")
    parser.add_argument("-sm", "--soundmetadata", action="store_true",
                        help="Flag: Save the sound / music metadata to a CSV file")
    #check if the defaults file exists
    if os.path.isfile(defaultsFilepath):
        args = parser.parse_args([defaults], namespace=nm)
    args = parser.parse_args(namespace=nm)
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
def downloadVideo(url, userID, videoID, dirName, prevCookies):
    #Make video filename using user ID and video ID
    fname = userID + " - " + videoID + ".mp4"
    filePath = os.path.join(dirName, fname)
    #print(filePath)
    #cookie = prevCookies[0]
    #print(cookie)
    rs = requests.Session()
    for cookie in prevCookies:
        #print(cookie)
        req_args = {"name": cookie["name"], "value": cookie["value"]}
        opt_args = {"domain": cookie["domain"],
            #"expires": cookie["expiry"],
            "rest": {"HttpOnly": cookie["httpOnly"]},
            "path": cookie["path"],
            "secure": cookie["secure"],
        }
        remadeCookie = requests.cookies.create_cookie(**req_args, **opt_args)
        rs.cookies.set_cookie(remadeCookie)

    #Check if a video with the same filename exists. Since we are using the
        #video ID in the filename, we can assume it will be the same video
        #If it exists, skip it. We don't want to download the same video again
        #Return False so metadata doesn't get saved again either
    if os.path.exists(filePath):
        print("File", fname, "already exists. Skipping download")
        return False

    #Try to download video file
    try:
        rs.headers.update({"User-Agent": USERAGENT})
        #print(rs.cookies)
        # with closing to ensure stream connection always closed
        with closing(rs.get(url, stream=True)) as r:
            if r.status_code == requests.codes.ok:
                # "wb" = open for write and as binary file
                #print("Sent:", r.request.headers)
                #print("Response:", r.headers)
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
                if not t:
                    continue
                else:
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
    captureVidMeta = False
    captureSoundMeta = False
    captureUserMeta = False
    baseURL = "https://tiktok.com"

    #define and get CLI args first
    args = setUpArgs()
    urls = []
    #Metadata headers
    VID_CSV_HEADERS = ["videoID", "userID", "userName", "sound", "caption",
                        "numLikes", "numComments", "timeAcquired", "url"]
    USER_CSV_HEADERS = ["userID", "userName", "numFollowing",
                        "numFans", "numHearts", "description", "url"]
    SOUND_CSV_HEADERS = ["title", "author", "numVideos", "url"]

    #check if user has provided download directory.
        #Create the default directory if needed
    if args.directory:
        directory = makeDir(args.directory)
    else:
        directory = makeDir("")
    if not directory:
        return

    captureVidMeta = True if args.videometadata else False
    captureUserMeta = True if args.usermetadata else False
    captureSoundMeta = True if args.soundmetadata else False

    #Check if user has provided list of URLs, single URL, or no URL
    if args.file:       #list of urls provided via CLI args
        urls = getURLsFromFile(args.file.strip())
    elif args.url:      #single url provided via CLI args
        urls.append(args.url.strip())
    else:               #if nothing provided via CLI args, ask for user input
        inputURL = input("TikTok page: ")
        if inputURL:
            urls.append(inputURL.strip())
        else:
            #If user didn't provide URL, abort
            print ("No URL entered.")
            return

    #Set up Chrome options to run headless then start Chrome webdriver with options
    options = webdriver.ChromeOptions()
    options.headless = True
    chrome = webdriver.Chrome(chrome_options=options)

    #start scraping each provided URL
    for url in urls:
        vidMetadata = {}
        userMetadata = {}
        soundMetadata = {}
        print("Scraping video from", url)
        try:
            chrome.get(url)

            currentCookies = chrome.get_cookies()
            #print(currentCookies)
            #video URL metadata
            pageURL = chrome.current_url.split("?")[0]
            vidMetadata["url"] = pageURL
            #print(pageURL)
        except WebDriverException as e:
            print("Chrome error: WebDriverException")
            raise e
            return

        #Pass the page source to BeautifulSoup for easier parsing
        page = BeautifulSoup(chrome.page_source, "html.parser")

        #check for missing video
        if page.find("div", class_ = "_error_page_"):
            print("Video removed (or check your URL)")
            continue

        #video URL to download
        videoURL = baseURL + page.find("video", class_ = "_video_card_").get("src")

        #video ID metadata
        videoID = pageURL.split("/")[-1]
        vidMetadata["videoID"] = videoID

        #user name metadata
        userName = page.find("h2", class_ = "_video_card_big_user_info_nickname").text
        vidMetadata["userName"] = userName
        userMetadata["userName"] = userName

        #user ID metadata
        userID = page.find("h2", class_ = "_video_card_big_user_info_handle").text[1:]
        #print(userID)
        vidMetadata["userID"] = userID
        userMetadata["userID"] = userID

        #user profile URL metadata
        userURL = baseURL + page.find("a", class_ = "_video_card_big_user_info_").get("href").split("?")[0]
        #print(userURL)
        userMetadata["url"] = userURL

        #sound title metadata
        sound = page.find("div", class_ = "_video_card_big_meta_info_music").a.text
        vidMetadata["sound"] = sound

        #sound URL metadata
        soundURL = baseURL + page.find("div", class_ = "_video_card_big_meta_info_music").a.get("href")
        soundMetadata["url"] = soundURL

        #caption metadata
        # if no caption is found, save empty string
        if(page.find("h2", class_ = "_video_card_big_meta_info_title")):
            caption = page.find("h2", class_ = "_video_card_big_meta_info_title").strong.text
        else:
            #print("no caption")
            caption = ""
        vidMetadata["caption"] = caption

        #video counts
        counts = page.find("div", class_ = "_video_card_big_meta_info_count").text
        countsRE = re.compile(r"^(\d+\.?\d?[k|m]?)\s\D+(\d+\.?\d?[k|m]?)")
        countsMatch = countsRE.match(counts)
        numVidLikes = ""
        numVidComments = ""
        if countsMatch:
            numVidLikes = countsMatch.group(1)
            numVidComments = countsMatch.group(2)
        vidMetadata["numLikes"] = numVidLikes
        vidMetadata["numComments"] = numVidComments
        #print(numVidLikes)
        #print(numVidComments)

        #timestamp metadata
        timestamp = readable = datetime.datetime.fromtimestamp(time.time()).isoformat()
        vidMetadata["timeAcquired"] = timestamp

        if captureUserMeta:
            chrome.get(userURL)
            page = BeautifulSoup(chrome.page_source, "html.parser")

            if page.find("div", class_ = "_error_page_"):
                print("User not found")
            else:
                #following metadata - assume order stays same
                userCounts = page.find("div", class_ = "_user_header_count")
                countsArray = userCounts.find_all("span", class_ = "_user_header_number")
                userFollowing = countsArray[0].text
                userFans = countsArray[1].text
                userHearts = countsArray[2].text
                userMetadata["numFollowing"] = userFollowing
                userMetadata["numFans"] = userFans
                userMetadata["numHearts"] = userHearts
                #print(userFollowing, userFans, userHearts)

                if(page.find("h2", class_ = "_user_header_desc").text):
                    userDesc = page.find("h2", class_ = "_user_header_desc").text
                    #print(userDesc)
                    userMetadata["description"] = userDesc

        if captureSoundMeta:
            chrome.get(soundURL)
            page = BeautifulSoup(chrome.page_source, "html.parser")

            if page.find("div", class_ = "_error_page_"):
                print("Sound not found")
            else:
                soundTitle = page.find("h1", class_ = "_music_header_title").text
                #print(soundTitle)
                authorSection = page.find("h1", class_ = "_music_header_author")
                if authorSection.span:
                    soundAuthor = authorSection.span.text
                elif authorSection.a:
                    soundAuthor = authorSection.a.text
                #print(soundAuthor)
                soundNumVid = page.find("span", class_ = "_music_header_number").text
                #print(soundNumVid)
                soundMetadata["title"] = soundTitle
                soundMetadata["author"] = soundAuthor
                soundMetadata["numVideos"] = soundNumVid

        #get video from URL scraped. send userID, videoID and DL directory
        if downloadVideo(videoURL, userID, videoID, directory, currentCookies):
            #only if video successfully downloaded, write metadata to file
            if captureVidMeta:
                writeMetadata(os.path.join(directory, VIDMETAFILENAME), VID_CSV_HEADERS, vidMetadata)
            if captureUserMeta:
                writeMetadata(os.path.join(directory, USERMETAFILENAME), USER_CSV_HEADERS, userMetadata)
            if captureSoundMeta:
                writeMetadata(os.path.join(directory, SOUNDMETAFILENAME), SOUND_CSV_HEADERS, soundMetadata)

    #Close Chrome properly
    chrome.quit()

if __name__ == "__main__":
    main()
