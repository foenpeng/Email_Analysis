# Email_Analysis
## This is a python code to parse one's mailbox to fetch the sending and receiving information and store them in a sqlite database. And it will use those information to draw a personal contact graph.

Instructions:

1 Go to https://takeout.google.com/settings/takeout
  Select Mail
  Click the button on the left of selecting sign
  Choose Select Labels
  Select the type of mails you want to analyze.
  Anything else as default and click Create Archive. It may take several hours to get the link to download the file
  
2 After you get the link from email, download the .mbox file and rename it as my_emails.mbox

3 Install anaconda and sqlite for your computer
  If the sqlite python connector is not pre-installed, in the shell, input "conda install -c blaze sqlite3=3.8.6"
  
4 move the attached email_analysis.py file into the same directory where you stored the .mbox file.
  open shell in that directory and input "python email_analysis.py"
  
5 Voila! Done!
