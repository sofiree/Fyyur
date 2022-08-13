#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from urllib import response
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment

import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import db, migrate, Show, Artist, Venue
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db.init_app(app)
migrate.init_app(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
    recentVenues= Venue.query.order_by(db.desc(Venue.id)).limit(10).all()
    recentArtists = Artist.query.order_by(db.desc(Artist.id)).limit(10).all()
    return render_template('pages/home.html', venues=recentVenues,artists=recentArtists )


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  areas = db.session.query(Venue.city, Venue.state).distinct(Venue.city, Venue.state)
  response = []
  for area in areas:

        # Querying venues and filter them based on area (city, venue)
        result = Venue.query.filter(Venue.state == area.state).filter(Venue.city == area.city).all()

        venue_data = []

        # Creating venues' response
        for venue in result:
            venue_data.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(db.session.query(Show).filter(Show.start_time > datetime.now()).all())
            })

            response.append({
                'city': area.city,
                'state': area.state,
                'venues': venue_data
            })

  return render_template('pages/venues.html', areas=response)



@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term', '')
  result = db.session.query(Venue).filter(Venue.name.ilike(f'%{search_term}%')).all()
  count = len(result)
  response = {
      "count": count,
      "data": result
  }
  for venue in result:
    response["data"].append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": venue.upcoming_shows_count
      })
  return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.filter(Venue.id == venue_id).first()

    past = db.session.query(Show).filter(Show.venue_id == venue_id).filter(
        Show.start_time < datetime.now()).join(Artist, Show.artist_id == Artist.id).add_columns(Artist.id, Artist.name,
                                                                                                Artist.image_link,
                                                                                                Show.start_time).all()

    upcoming = db.session.query(Show).filter(Show.venue_id == venue_id).filter(
        Show.start_time > datetime.now()).join(Artist, Show.artist_id == Artist.id).add_columns(Artist.id, Artist.name,
                                                                                                Artist.image_link,Show.start_time).all()
    upcoming_shows = []
    past_shows = []
    for i in upcoming:
        upcoming_shows.append({
            'artist_id': i[1],
            'artist_name': i[2],
            'image_link': i[3],
            'start_time': str(i[4])
        })

    for i in past:
        past_shows.append({
            'artist_id': i[1],
            'artist_name': i[2],
            'image_link': i[3],
            'start_time': str(i[4])
        })

    if venue is None:
       abort(404)

    response = {
        "id": venue.id,
        "name": venue.name,
        "genres": [venue.genres],
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past),
        "upcoming_shows_count": len(upcoming),
      }                                                                                        
    return render_template('pages/show_venue.html', venue=response)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
   
  new_venue = Venue()
  new_venue.name=request.form['name']
  new_venue.city=request.form['city']
  new_venue.state=request.form['state']
  new_venue.address=request.form['address']
  new_venue.phone=request.form['phone']
  new_venue.genres=request.form['genres']
  new_venue.image_link=request.form['image_link']
  new_venue.facebook_link=request.form['facebook_link']
  new_venue.website=request.form['website']
  # venue.seeking_talent=json.loads(request.form['seeking_talent'].lower()),
  # venue.seeking_description=request.form['seeking_description']
  
  try:
    db.session.add(new_venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully added!')
  except Exception as e:
    print(e)
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be added')
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')



# update
# ------------------------------

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.filter(Venue.id == venue_id).one_or_none()
  if venue is None:
        abort(404)

  venue = venue.serialize
  form = VenueForm(data=venue)

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  venue = Venue.query.filter(Venue.id==venue_id).one()
  venue.name = request.form['name']
  venue.address = request.form['address']
  venue.genres = request.form['genres']  # array json
  venue.city = request.form['city']
  venue.state = request.form['state']
  venue.phone = request.form['phone']
  venue.facebook_link = request.form['facebook_link']
  # venue.image_link = request.form['image_link']
  try:
    db.session.commit()
        # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except Exception as e:
      db.session.rollback()
      flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  response = Artist.query.all()
  return render_template('pages/artists.html', artists=response)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term', '')
  result = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
  count = len(result)
  response = {
        "count": count,
        "data": result
    }
  for artist in result:
    response['data'].append({
    "id": artist.id,
    "name": artist.name,
    "num_upcoming_shows": artist.upcoming_shows_count,
    })
  return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
    artist = Artist.query.filter(Artist.id == artist_id).first()
  
    past = db.session.query(Show).filter(Show.artist_id == artist_id).filter(
        Show.start_time < datetime.now()).join(Venue, Show.venue_id == Venue.id).add_columns(Venue.id, Venue.name,
                                                                                             Venue.image_link,
                                                                                             Show.start_time).all()

    upcoming = db.session.query(Show).filter(Show.artist_id == artist_id).filter(
        Show.start_time > datetime.now()).join(Venue, Show.venue_id == Venue.id).add_columns(Venue.id, Venue.name,
                                                                                             Venue.image_link,
                                                                                             Show.start_time).all()

    upcoming_shows = []

    past_shows = []

    for i in upcoming:
        upcoming_shows.append({
            'venue_id': i[1],
            'venue_name': i[2],
            'image_link': i[3],
            'start_time': str(i[4])
        })

    for i in past:
        past_shows.append({
            'venue_id': i[1],
            'venue_name': i[2],
            'image_link': i[3],
            'start_time': str(i[4])
        })

    if artist is None:
        abort(404)

    response = {
        "id": artist.id,
        "name": artist.name,
        "genres": [artist.genres],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past),
        "upcoming_shows_count": len(upcoming),
    }
    return render_template('pages/show_artist.html', artist=response)

#  Update
#  ----------------------------------------------------------------

@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.filter(Artist.id == artist_id).one_or_none()
  if artist is None:
        abort(404)

  artist = artist.serialize
  form = ArtistForm(data=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)



@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)
 
  artist = Artist.query.filter(Artist.id==artist_id).one()
  artist.name = request.form['name']
  artist.genres = request.form['genres'] # array json
  artist.city = request.form['city']
  artist.state = request.form['state']
  artist.phone = request.form['phone']
  artist.facebook_link = request.form['facebook_link']
  artist.image_link = request.form['image_link']
  artist.update()
  try:
    db.session.commit()
        # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except Exception as e:
      db.session.rollback()
      flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be updated.')

  finally:
    db.session.close()
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  return redirect(url_for('show_artist', artist_id=artist_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

   
    artist = Artist()
    artist.name=request.form['name']
    artist.city=request.form['city']
    artist.state=request.form['state']
    artist.phone=request.form['phone']
    artist.genres=request.form['genres']
    artist.image_link=request.form['image_link']
    artist.facebook_link=request.form['facebook_link']
    # artist.seeking_venue=json.loads(request.form['seeking_venue'].lower()),
    artist.website=request.form['website']
    artist.seeking_description=request.form['seeking_description']
    try:
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        print(e)
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be added')
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = Show.query.join(Artist, Artist.id == Show.artist_id).join(Venue, Venue.id == Show.venue_id).all()

  response = []
  for show in data:
        response.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)
        })
  return render_template('pages/shows.html', shows=response)



# Create
# --------------
@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  show = Show()
  show.artist_id=request.form['artist_id']
  show.venue_id=request.form['venue_id']
  show.start_time=request.form['start_time']
  try:
    db.session.add(show)
    # update venue and artist table
    updated_artist = Artist.query.get(show.artist_id)
    updated_venue = Venue.query.get(show.venue_id)
    if(show.upcoming):
      updated_artist.upcoming_shows_count += 1;
      updated_venue.upcoming_shows_count += 1;
    else:
      updated_artist.past_shows_count += 1;
      updated_venue.past_shows_count += 1;
      db.session.commit()
      flash('Show was successfully added!')
  except Exception as e:
    print(e)
    flash('An error occurred. Show could not be added')
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')


# error handelers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
# if __name__ == '__main__':
    # app.run()

# run with debugger 
if __name__ == '__main__':
    app.run(debug=True)

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
