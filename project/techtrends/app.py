import sqlite3
import logging, sys

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# DB connections counter
db_conns = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    global db_conns
    # We are set to count each connection to the database
    db_conns += 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      logger.info('Non existing article is accessed!')
      return render_template('404.html'), 404
    else:
      logger.info('Acticle "%s" retrieved!', post['title'])
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logger.info('About page is retrieved.')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            logger.info("The article titled as '" + title + "' was created.")

            return redirect(url_for('index'))

    return render_template('create.html')

# Healthcheck endpoint
# Should return status code 200 and the response: "result: OK - healthy"
# Added: Standout Sugestion 1: Dynamic Healthcheck endpoint, will check if the table 'posts' exists in DB
@app.route('/healthz')
def healthz():
    try:
        connection = get_db_connection()
        connection.execute('SELECT * FROM posts').fetchone()
        response = app.response_class(
            response=json.dumps({"result": "OK - healthy"}),
            status=200,
            mimetype='application/json'
        )
    except:
        response = app.response_class(
            response=json.dumps({"result": "ERROR - unhealthy"}),
            status=500,
            mimetype='application/json'
        )
    finally:
        connection.close()

    return response

# Metrics endpoint
# Should return status code 200 and JSON response with total amount of posts and total amount of connections to the DB
# Example output: {"db_connection_count": 1, "post_count": 7}
@app.route('/metrics')
def metrics():
    connection = get_db_connection()

    # We can use the length of a returning object
    #posts_count = len((connection.execute('SELECT * FROM posts').fetchall()))

    # But I think more optimal will be performing the count of rows on a DB side
    posts_count = connection.execute('SELECT COUNT(*) from posts').fetchone()[0]

    connection.close()
    global db_conns
    response = app.response_class(
        response=json.dumps({"db_connection_count": db_conns, "post_count": posts_count}),
        status = 200,
        mimetype='application/json'
    )
    return response

# Some IDE's like Pycharm starts the Flask application a bit different, like wrapping and starting with 'flask run',
# hence the following body of 'if' section is ignored, as the value of '__name__' variable is not '__main__', but 'techtrends.app' as in my case.
# Thus I decided to leave logging settings beyond that 'if' section, where the code in all cases will be executed.
##logging.basicConfig(level=logging.DEBUG, format = '%(levelname)s:%(name)s:%(asctime)s, %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create STDOUT handler
stdouth = logging.StreamHandler(sys.stdout)
stdouth.setLevel(logging.DEBUG)
# create STDERR handler
stderrh = logging.StreamHandler(sys.stderr)
stderrh.setLevel(logging.DEBUG)
# create formatter and add it to both handlers
formatter = logging.Formatter('%(levelname)s:%(name)s:%(asctime)s, %(message)s', datefmt='%m/%d/%Y, %H:%M:%S')
stdouth.setFormatter(formatter)
stderrh.setFormatter(formatter)
# add handlers to logger
logger.addHandler(stdouth)
logger.addHandler(stderrh)

# start the application on port 3111
if __name__ == "__main__":
    app.run(host='0.0.0.0', port='3111')

