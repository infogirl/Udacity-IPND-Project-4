import cgi
import urllib
import webapp2

from google.appengine.ext import ndb
from google.appengine.api import users

import jinja2
import os


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

DEFAULT_WALL = 'Public'

def wall_key(wall_name=DEFAULT_WALL):
#Constructs a Datastore key for a Wall entity.
  return ndb.Key('Wall', wall_name)

class Name(ndb.Model):
# Sub model for representing an author of the comment
  identity = ndb.StringProperty(indexed=True)
  name = ndb.StringProperty(indexed=False)
  email = ndb.StringProperty(indexed=False)

class Comment(ndb.Model):
#The main model for representing an individual post entry."""
  name = ndb.StructuredProperty(Name)
  content = ndb.StringProperty(indexed=False)
  date = ndb.DateTimeProperty(auto_now_add=True)

#Functions to Handler Class
class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
#Takes template and parameters and use jinja environment
#to create file, load file and pass in the paramters and
#return a string
    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)
#Takes the template and parameters
#and calls render and wraps it in self.write
    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class MainPage(Handler):
  def get(self):
    wall_name = self.request.get('wall_name',DEFAULT_WALL)
    if wall_name == DEFAULT_WALL.lower(): wall_name = DEFAULT_WALL
    #Get comments from datastore and put them in order by date
    comments_query = Comment.query(ancestor = wall_key(wall_name)).order(-Comment.date)
    comments =  comments_query.fetch()

    #If a person is logged into Google's Services
    user = users.get_current_user()
    if user:
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
    else:
        url_linktext = 'Login'
        user_name = 'Anonymous Poster'

    sign_query_params = urllib.urlencode({'wall_name': wall_name})

    #Render the template and variables
    template = jinja_env.get_template('index.html')
    self.render("index.html", comments=comments, users=users)

class PostWall(webapp2.RequestHandler):
    def post(self):
        wall_name = self.request.get('wall_name',DEFAULT_WALL)
        comment = Comment(parent=wall_key(wall_name))

    # When the person is making the post, check to see whether the person
    # is logged into Google
        if users.get_current_user():
            comment.name = Name(
                identity=users.get_current_user().user_id(),
                name=users.get_current_user().nickname(),
                email=users.get_current_user().email())
        else:
            comment.name = Name(
                name='anonymous@anonymous.com',
                email='anonymous@anonymous.com')
    # Get the content from our request parameters and post/store the comment
        comment.content = self.request.get('content')
        comment.put()

    #page redirect
        self.redirect('/?wall_name=' + wall_name)


app = webapp2.WSGIApplication(  [
  ('/', MainPage),
  ('/sign', PostWall),
], debug=True)