__author__ = 'Satshabad Khalsa'

try:
    import mechanize
except ImportError:
    print 'Please install the mechanize library (sudo pip install mechanize)'
    exit()

import cookielib

try:
    import BeautifulSoup
except ImportError:
    print 'Please install the BeautifulSoup library (sudo pip install BeautifulSoup)'
    exit()

import os

try:
    import docopt
    from docopt import docopt
except ImportError:
    print 'Please install the docopt library (sudo pip install docopt)'
    exit()

import sys

def main():
    '''"Usage: songkickscraper.py [options]

    Options:
    -h --help      Show this
    -d <path>      The full path to the directory containing folders named after artists you want to track
    -u <username>  Your SongKick username
    -p <password>  Your SongKick password
    -f <file>      A file with a list of artists to track, one per line.
    -o <file>      The file to contain the results of the operation. [default: results.txt]

    '''

    # option parsing
    options, arguments = docopt(main.__doc__, help=True)

    if not options.u:
        print 'Please provide a SongKick username using -u'
        exit()
    if not options.p:
        print "Please provide a SongKick password using -p (this is not stored anywhere)"
        exit()
    if not options.d and not options.f:
        print 'Please provide a source of artists\n ' \
              'either a file (one per line) with the -f option\n ' \
              'or a directory containing artists folders with the -d option'
        exit()


    # Browser
    br = mechanize.Browser()



    # Cookie Jar
    cj = cookielib.LWPCookieJar()
    br.set_cookiejar(cj)

    # Browser options
    br.set_handle_equiv(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)

    # To not get blocked
    br.addheaders = [('User-agent',
                      'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

    br.open('http://www.songkick.com/session/new')

    # This is the login form
    br.select_form(nr=1)

    br.form['username_or_email'] = options.u
    br.form['password'] = options.p
    br.find_control(name="persist").value = ["y"]
    br.submit()

    # error checking
    if 'Sorry, that username or password is incorrect' in br.response().read():
        print 'Sorry, that username or password is incorrect'
        exit()

    # Get all of the users so far tracked artists
    trackedArtists = set()
    morePages = True
    i = 1

    # so that we run off the end of the artist pages
    br.set_handle_redirect(False)
    print 'Getting currently tracked artists. This may take a while if you have many...\n'

    while morePages:
        try:
            br.open('http://www.songkick.com/tracker/artists?page=' + str(i))
        except mechanize.HTTPError:
            morePages = False
        soup = BeautifulSoup.BeautifulSoup(br.response().read())

        # find the artist link
        links = soup.findAll(attrs={'href': BeautifulSoup.re.compile('/artists/*[^?]')})
        for link in links:
            # find the unique artist number
            trackedArtists.add(BeautifulSoup.re.findall(r'/artists/([0-9]+)*[^?]', link.attrMap['href'])[0])
        i += 1

        # display progress to user
        sys.stdout.write('\rFound ' + str(len(trackedArtists)) + ' artists so far')
        sys.stdout.flush()

        if trackedArtists.issubset(set()):
            morePages = False

    artistsToGet = []
    if options.d:
        artistsToGet = set([name for name in os.listdir(options.d)])
    else:
        artistsToGet = set([line[:-1] for line in open(options.f).readlines()])

    print '\n\nNow tracking artists\n'

    # track the artists the user gives us

    unfoundArtists = []
    sucessArtists = []
    alreadyTrackedArtists = []
    br.set_handle_redirect(True)
    for i, artist in enumerate(artistsToGet):
        sys.stdout.write('\rTracking '+ str(i) + ' of ' + str(len(artistsToGet)))
        sys.stdout.flush()
        # search for artist
        br.open('http://www.songkick.com/search?query=' + '+'.join(artist.split()))
        soup = BeautifulSoup.BeautifulSoup(br.response().read())

        # if there is no artist by that name
        if soup.findAll(attrs={'href': BeautifulSoup.re.compile('/artists/*[^?]')}) == []:
            unfoundArtists.append(artist)
        else:

            # take the first artists result
            link = soup.findAll(attrs={'href': BeautifulSoup.re.compile('/artists/*[^?]')})[1]

            # check that the user is not already following this artist
            if not BeautifulSoup.re.findall(r'/artists/([0-9]+)*[^?]', link.attrMap['href'])[0] in trackedArtists:
                br.open('http://www.songkick.com/search?query=' + '+'.join(artist.split()))
                br.select_form(nr=2)
                br.submit()
                sucessArtists.append(link.text)
            else:
                alreadyTrackedArtists.append(link.text)



    # write out the results
    results = open(options.o, 'w')
    results.write('Artists that were successfully tracked:\n')
    for artist in sucessArtists:
        results.write(artist + '\n')

    results.write('\nArtists that could not be found on SongKick:\n')
    for artist in unfoundArtists:
        results.write(artist + '\n')

    results.write('\nArtists that were already tracked:\n')
    for artist in alreadyTrackedArtists:
        results.write(artist + '\n')

    print '\n\nDone, results written to', options.o

main()