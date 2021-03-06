__author__ = 'Satshabad Khalsa'

try:
    import mechanize
except ImportError:
    print 'Please install the mechanize library (sudo pip install mechanize)'
    exit()

import pickle

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
    trackedArtistsByNumber = set()
    trackedArtistsByName = set()
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
            trackedArtistsByNumber.add(BeautifulSoup.re.findall(r'/artists/([0-9]+)*[^?]', link.attrMap['href'])[0])
            #find the artists name
            trackedArtistsByName.add(link.text)
        i += 1

        # display progress to user
        sys.stdout.write('\rFound ' + str(len(trackedArtistsByNumber)) + ' artists so far')
        sys.stdout.flush()

        if trackedArtistsByNumber.issubset(set()):
            morePages = False

    # get the artists to track, if there was a previously tracked directory, just get the new artists.
    artistsToGet = []
    try:
        unp = pickle.Unpickler(open('.tracked'))
        prevArtistsDict = unp.load()
    except:
        prevArtistsDict = {}

    if options.d:
        artistsToGet = set([unicode(name) for name in os.listdir(options.d)])
        placeToLoadFrom = options.d
    else:
        artistsToGet = set([unicode(line[:-2]) for line in open(options.f).readlines()])
        placeToLoadFrom = options.f

    if prevArtistsDict.has_key(placeToLoadFrom):
        artistsToGet = artistsToGet - prevArtistsDict[placeToLoadFrom]
        prevArtistsDict[placeToLoadFrom] = artistsToGet.union(prevArtistsDict[placeToLoadFrom])
    else:
        prevArtistsDict[placeToLoadFrom] = artistsToGet

    # hopefully remove all the artists that have been just found on the users
    artistsToGet = artistsToGet - trackedArtistsByName



    print '\n\nNow tracking artists\n'

    # track the artists the user gives us

    unfoundArtists = []
    sucessArtists = []
    alreadyTrackedArtists = []
    br.set_handle_redirect(True)
    try:
        for i, artist in enumerate(artistsToGet):
            sys.stdout.write('\rTracking '+ str(i+1) + ' of ' + str(len(artistsToGet)))
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
                if not BeautifulSoup.re.findall(r'/artists/([0-9]+)*[^?]', link.attrMap['href'])[0] in trackedArtistsByNumber:
                    br.open('http://www.songkick.com/search?query=' + '+'.join(artist.split()))
                    br.select_form(nr=2)
                    br.submit()
                    sucessArtists.append(link.text)
                else:
                    alreadyTrackedArtists.append(link.text)
    except:
        print '\nsomething went wrong, but what did get done is written out to', options.o

    # save the artist that were tracked so next time they wont be tracked again.
    p = pickle.Pickler(open('.tracked', 'w'))

    # if in directory mode dump dir records
    if options.d:
        p.dump(prevArtistsDict)

    # write out the results
    results = open(options.o, 'w')
    results.write('Artists that were successfully tracked:\n')
    for artist in sucessArtists:
        results.write(artist + '\n')

    results.write('\nArtists that could not be found on SongKick:\n')
    for artist in unfoundArtists:
        results.write(artist + '\n')

    results.write('\nArtists we tried to track but were already tracked:\n')
    for artist in alreadyTrackedArtists:
        results.write(artist + '\n')

    print '\n\nDone, results written to', options.o

main()