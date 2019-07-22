# Tiktok Video Downloader

Provide a Tiktok short URL (vm.tiktok.com), old share URL (www.tiktok.com/share/video), or new user video URL (www.tiktok.com/@USERID/video) to download the video.

Likely works with mobile site url (m.tiktok.com), but not tested.

URLs can be provided in a text file list (one URL per line) with the -f command line argument, a single URL with the -u command line argument, or not providing either will prompt the user to enter a single URL after executing the script.

Using the -d command line will allow you to choose the directory to save the video (and metadata) to.

Saving video metadata, user metadata, and sound metatdata are option and off by default. They can be toggled on with their corresponding command line arguments. It is important to note that capturing user and sound metadata will increase the time to download the video as the script gets the metadata from additional URLs. Currently, duplicate user and sound metadata will all be captured. This will change in the future so this metadata is only updated instead of saved multiple times.

A file can be created called "defaults" (no file extension) in the directory the script is in, that when command line arguments are written one per line, these arguments will be used as the default options for every video download. This is useful if you have a specific directory you like to download to (-d) and know your metadata capture preferences (-vm, -um, -sm) will remain the same.
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
