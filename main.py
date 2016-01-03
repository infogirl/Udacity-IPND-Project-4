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

class Comment(ndb.Model):
#The main model for representing an individual post entry.
  name = ndb.StringProperty(indexed=True)
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

class Error(Handler):
  def get(self):
    self.render("error.html")

class MainPage(Handler):
  def get(self):
    wall_name = self.request.get('wall_name',DEFAULT_WALL)
    if wall_name == DEFAULT_WALL.lower(): wall_name = DEFAULT_WALL
    #Get comments from datastore and put them in order by date
    comments_query = Comment.query(ancestor = wall_key(wall_name)).order(-Comment.date)
    comments =  comments_query.fetch()

    sign_query_params = urllib.urlencode({'wall_name': wall_name})

    #Render the template and variables
    self.render("index.html", comments=comments, users=users)

class PostWall(webapp2.RequestHandler):
    def post(self):
        wall_name = self.request.get('wall_name',DEFAULT_WALL)
        comment = Comment(parent=wall_key(wall_name))
        #get the content and user from the form
        comment.content = self.request.get('content')
        comment.name= self.request.get('user')
        #Validate the input
        if len(comment.name)!=0 and len(comment.content)!=0:
          comment.put()
          self.redirect('/')
        else:
          self.redirect('/error')

app = webapp2.WSGIApplication(  [
  ('/', MainPage),
  ('/sign', PostWall),
  ('/error', Error)
], debug=True)