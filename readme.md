# Tiktok Video Downloader

Provide a Tiktok short URL (vm.tiktok.com), old share URL (www.tiktok.com/share/video), or new share URL (www.tiktok.com/@USERID/video) to download the video.

Possibly works with mobile site url (m.tiktok.com), but not tested.

URLs can be provided in a text file list (one URL per line) with the -f command line argument, a single URL with the -u command line argument, or not providing either will prompt the user to enter a single URL after executing the script.

```
usage: videoScrape.py [-h] [-d DIRECTORY] [-u URL] [-f [FILE]] [-vm] [-um]
                      [-sm]

If providing a 'defaults' file, arguments must be one per line

optional arguments:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        (Parent) Directory to download videos to
  -u URL, --url URL     Single URL to scrape video from
  -f [FILE], --file [FILE]
                        Specify a .txt file with a list of URLs to scrape
  -vm, --videometadata  Flag: Save the video metadata to a CSV file
  -um, --usermetadata   Flag: Save the user / creator metadata to a CSV file
  -sm, --soundmetadata  Flag: Save the sound / music metadata to a CSV file
```

It's possible that recent tiktok updates require cookies and user agent to be provided to (down)load the video, so those are preserved and used.
