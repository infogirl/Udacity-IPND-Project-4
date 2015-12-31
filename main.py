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


class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class MainPage(webapp2.RequestHandler):
  def get(self):
    wall_name = self.request.get('wall_name',DEFAULT_WALL)
    if wall_name == DEFAULT_WALL.lower(): wall_name = DEFAULT_WALL

    comments_query = Comment.query(ancestor = wall_key(wall_name)).order(-Comment.date)
    comments =  comments_query.fetch()

    # If a person is logged into Google's Services
    user = users.get_current_user()
    if user:
        url = users.create_logout_url(self.request.uri)
        url_linktext = 'Logout'
        user_name = user.nickname()
    else:
        url = users.create_login_url(self.request.uri)
        url_linktext = 'Login'
        user_name = 'Anonymous Poster'

        template_values = {
        'user' : user,
        'comments' : comments,
        'url' : url,
        'url_linktext' : url_linktext,
        }
        return template_values

    # Create our comments html
    comments_html = ''
    for comment in comments:
        if user and user.user_id() == comment.name.identity:
            posts_html += '<div><h3>(You) ' + comment.name.name + '</h3>\n'
        else:
            posts_html += '<div><h3>' + comment.name.name + '</h3>\n'

        posts_html += 'wrote: <blockquote>' + cgi.escape(comment.content) + '</blockquote>\n'
        posts_html += '</div>\n'

    sign_query_params = urllib.urlencode({'wall_name': wall_name})

    template = jinja_env.get_template('index.html')
    self.response.out.write(template.render(get.template_values))
    #self.render(templates)
    #self.response.out.write(template)

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
                name='anonymous@anonymous.com'
                email='anonymous@anonymous.com')
    # Get the content from our request parameters, in this case, the message
    # is in the parameter 'content'
        comment.content = self.request.get('content')
        comment.put()

    # Do other things here such as a page redirect
        self.redirect('/?wall_name=' + wall_name)


app = webapp2.WSGIApplication(  [
  ('/', MainPage),
  ('/sign', PostWall),
], debug=True)
