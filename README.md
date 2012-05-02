# Track-Songkick-Artists


###Automatically track a list of artists on songkick

I used to use Songkick's iTunes tracker to track all of my favorite band's tours, but they discontinued that service a while back so I wrote this.

The goal of this program is to tell Songkick to track every artist in your music library.


## Usage

To track a bunch of artists all at once, **list them in a file**, one per line, and run:

    $ python AutoTracker.py -u <username> -p <password> -f <filename.txt> 
    
Or if you have all of your music organized in **folders by artist** you can track them all like this:

    $ python AutoTracker.py -u <username> -p <password> -d <directory-holding-artists>
    
If you would like the results written out to a special file, run this:

    $ python AutoTracker.py -u <username> -p <password> -d <directory-holding-artists> -o <myresults.txt>
    
Simple as that

## Dependencies

To run this program you will need these external libraries

* BeautifulSoup
* mechanize
* docopt

You can get these through pip like so:

    $ sudo pip install BeautifulSoup
    $ sudo pip install mechanize
    $ sudo pip install docopt
    
You can also install these through easy_install
