#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import datetime
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify,abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(),unique=True,nullable=False)
    city = db.Column(db.String(120),nullable=False)
    state = db.Column(db.String(120),nullable=False)
    address = db.Column(db.String(120),nullable=False)
    phone = db.Column(db.String(120),nullable=False)
    genres = db.Column(db.String(120),nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean(), default=True)
    seeking_description = db.Column(db.String())
    website = db.Column(db.String())
    shows = db.relationship(
        "Show", backref=db.backref("venue_shows", lazy=True))

    def __repr__(self):
      return f"<Venue ID :{self.id} name :{self.name} />"
    def get_venue(self):
      upcoming_shows_query=Show.query.filter(Show.venue_id==self.id).filter(Show.start_time>datetime.now()).all()
      return {'id':self.id,'name':self.name,'upcoming_shows_count':len(upcoming_shows_query)}
    # TODO: implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(),unique=True,nullable=False)
    city = db.Column(db.String(120),nullable=False)
    state = db.Column(db.String(120),nullable=False)
    phone = db.Column(db.String(120),nullable=False)
    genres = db.Column(db.String(120),nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean(), default=True)
    seeking_description = db.Column(db.String())
    website = db.Column(db.String())
    shows = db.relationship(
        "Show", backref=db.backref("artist_shows", lazy=True))
    def __repr__(self):
      return f"<Artist ID :{self.id} name :{self.name} />"
    def get_artist(self):
      upcoming_shows_query=Show.query.filter(Show.artist_id==self.id).filter(Show.start_time>datetime.now()).all()
      return {'id':self.id,'name':self.name,'upcoming_shows_count':len(upcoming_shows_query)}
    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


class Show (db.Model):
  __tablename__ = 'shows'
  id = db.Column(db.Integer, primary_key=True)
  venue_id = db.Column(db.Integer, db.ForeignKey('venues.id'), nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey(
      'artists.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)
  def __repr__(self):
    return f"<Show ID :{self.id} date :{self.start_time} />"

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format = "EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format = "EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[]
  places=Venue.query.distinct('city','state').all()
  for place in places:
    venues = Venue.query.filter(Venue.state==place.state).filter(Venue.city==place.city).all()
    row={
      'city': place.city,
      'state':place.state,
      'venues':[venue.get_venue() for venue in venues]
    }
    data.append(row)
  return render_template('pages/venues.html', areas=data);


@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  searchingFor = request.form.get('search_term')
  formated="%{}%".format(searchingFor)
  data=Venue.query.filter(Venue.name.ilike(formated))
  print(data)
  response = {
    "count": data.count(),
    "data": [venue.get_venue() for venue in data]
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.filter_by(id=venue_id).first_or_404()
  upcoming_shows_query=db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  past_shows_query=db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  data=venue.__dict__
  upcoming_shows_list=[]
  past_shows_list=[]
  
  for j in past_shows_query:
    past_shows_list.append({
          "artist_id": j.artist_id,
          "artist_name": j.artist_shows.name,
          "artist_image_link": j.artist_shows.image_link,
          "start_time": j.start_time.strftime("%m/%d/%Y, %H:%M")
        })
  data['past_shows']=past_shows_list
  data['past_shows_count']=len(past_shows_list)

  for i in upcoming_shows_query:
    upcoming_shows_list.append({
          "artist_id": i.artist_id,
          "artist_name": i.artist_shows.name,
          "artist_image_link": i.artist_shows.image_link,
          "start_time": i.start_time.strftime("%m/%d/%Y, %H:%M")
        })
  data['upcoming_shows']=upcoming_shows_list
  data['upcoming_shows_count']=len(upcoming_shows_list)
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error=False
  # TODO: insert form data as a new Venue record in the db, instead
  try:
    venue=Venue(name=request.form['name'],city=request.form['city'],state=request.form['state'],address=request.form['address'],phone=request.form['phone'],genres=request.form['genres'],facebook_link=request.form['facebook_link'])
    db.session.add(venue)
    db.session.commit()
  # TODO: modify data to be the data object returned from db insertion
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  except:
    db.session.rollback()
    error=True
  finally:
    db.session.close()
    if error:
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed , maybe is duplicated')
      return redirect(url_for("venues"))
    else:
      return redirect(url_for("venues"))
 
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  error=False
  try:
      venue=Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
  except:
      db.session.rollback()
      error=True
  finally:
      db.session.close()
      if error:
        flash('An error occurred. Venue with the ID  ' + venue_id+ ' could not be deleted.')
      
  return render_template('pages/home.html')


  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists=Artist.query.all()
  data=[]
  for artist in artists:
    data.append({
      "id":artist.id,
      "name":artist.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  searchingFor = request.form.get('search_term')
  formated="%{}%".format(searchingFor)
  data=Artist.query.filter(Artist.name.ilike(formated))
  print(data)
  # response={}
  response = {
    "count": data.count(),
    "data": [artist.get_artist() for artist in data]
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  artist = Artist.query.filter_by(id=artist_id).first_or_404()
  upcoming_shows_query=db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  past_shows_query=db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()
  data=artist.__dict__
  upcoming_shows_list=[]
  past_shows_list=[]
  
  for j in past_shows_query:
    past_shows_list.append({
          "venue_id": j.venue_id,
          "venue_name": j.venue_shows.name,
          "venue_image_link": j.venue_shows.image_link,
          "start_time": j.start_time.strftime("%m/%d/%Y, %H:%M")
        })
  data['past_shows']=past_shows_list
  data['past_shows_count']=len(past_shows_list)

  for i in upcoming_shows_query:
    upcoming_shows_list.append({
          "venue_id": i.venue_id,
          "venue_name": i.venue_shows.name,
          "venue_image_link": i.venue_shows.image_link,
          "start_time": i.start_time.strftime("%m/%d/%Y, %H:%M")
        })
  data['upcoming_shows']=upcoming_shows_list
  data['upcoming_shows_count']=len(upcoming_shows_list)
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist=Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  try:
    artist=Artist.query.get(artist_id)
    artist.name=request.form['name']
    artist.city=request.form['city']
    artist.state=request.form['state']
    artist.phone=request.form['phone']
    artist.genres=request.form['genres']
    artist.facebook_link=request.form['facebook_link']
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue=Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  try:
    venue=Venue.query.get(venue_id)
    venue.name=request.form['name']
    venue.city=request.form['city']
    venue.state=request.form['state']
    venue.address=request.form['address']
    venue.phone=request.form['phone']
    venue.genres=request.form['genres']
    venue.facebook_link=request.form['facebook_link']
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))

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
  error=False
  try:
    artist=Artist(name=request.form['name'],city=request.form['city'],state=request.form['state'],phone=request.form['phone'],genres=request.form['genres'],facebook_link=request.form['facebook_link'])
    db.session.add(artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    error=True
  finally:
    db.session.close()
    if error:
      flash('Artist ' + request.form['name'] + '  failed !! maybe is  duplicated !! ')
      return redirect(url_for("artists"))
    else:
      return redirect(url_for("artists"))
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  # upcoming_shows_query=db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  shows=db.session.query(Show).join(Artist).join(Venue).all()
  data=[]
  for show in shows:
    data.append({
      "venue_id":show.venue_shows.id,
      "venue_name":show.venue_shows.name,
      "artist_id":show.artist_shows.id,
      "artist_name":show.artist_shows.name,
      "artist_image_link":show.artist_shows.image_link,
      "start_time":show.start_time.strftime("%m/%d/%Y, %H:%M")

    })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  error=False
  try:
    show=Show(venue_id=request.form["venue_id"],artist_id=request.form['artist_id'],start_time=request.form['start_time'])
    db.session.add(show)
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    error=True
  finally:
    db.session.close()
    if error:
      flash('error  : show operation failed !!')
      return redirect(url_for("shows"))
    else:
      return redirect(url_for("shows"))
  # on successful db insert, flash success
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/

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
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
