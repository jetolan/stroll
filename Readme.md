# Building a stroll score from a model of open business, etc.


Pulls data from an csv of crime data and displays as Google maps heatmap in the location you request. 

Currently, the score is the number of crimes on a particular block. The crime data I'm using is only from 10-2016 -> 02-2017, so it is pretty limited. We'll want to add open business', etc.

Currently the input time does not affect the output.

## Examples:

example.py shows how to get scores in a grid of locations near a particular address at a particular time:


## Web

The web interface uses Flask to display the results of make_grid_of_scores over a google map. Flask makes it simple to use python as an interface on an html page: You can look in web/stroll/views.py to see where make_grid_of_scores is called with input from the html page.


Below are some additional notes in that go throught the process of deploying the web folder to a amazon ec2 instance.


<pre>

Create an Amazon EC2 instance.

You can ssh into in with

OK.

Install pandas, etc:
sudo pip install pandas
sudo pip install patsy
(http://www.scipy.org/install.html)
sudo apt-get install python-numpy python-scipy python-matplotlib

sudo pip install sklearn

OK.

You can by a DN on godaddy (etc), so that you can have an address (like stroll.net) point to your amazon ec2 static ip address.
just added aws ec2 ip address on godaddy...might need to do more..

To setup flask on the AWS instance follow:
http://dylanstorey.com/2016/06/Flask_and_AWS.html

</pre>


## Running the webpage locally

To start the webpage locally, open a Terminal, navigate to the stroll/web directory, and start Flask running in the background:

$python run.py

(Note that you may need to install some python packages on you local computer if the python call gives errors)

Then point your brower to http://127.0.0.1:5000/

