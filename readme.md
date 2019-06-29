# Tiktok Video Downloader

Provide a Tiktok short URL (vm.tiktok.com), old share URL (www.tiktok.com/share/video), or new share URL (www.tiktok.com/@USERID/video) to download the video.
Possibly works with mobile site url (m.tiktok.com), but not tested.

URLs can be provided in a text file list (one URL per line) with the -f command line argument, a single URL with the -u command line argument, or not providing either will prompt the user to enter a single URL after executing the script.

The -d command line argument will allow the user to specify a download location. Not providing this will download the video to the [home directory]/Videos/TikTok folder by default.

New tiktok updates require cookies and user agent to be provided to (down)load the video.
