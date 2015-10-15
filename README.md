# tradebindr.com

A site to help you find other nearby people to trade Magic: The Gathering cards with.

### Local Development Setup

1. `pip install virtualenv` if you don't already have it
1. `cd tradebindr` go to wherever you cloned the repo
1. `virtualenv venv` create a virtualenv
1. `source venv/bin/activate` activate the virtualenv
1. `pip install -r requirements.txt` to install all python dependencies
1. Install Postgres 9.3 or higher. On Mac it may be easier to use [Postgres.app](http://postgresapp.com) but I haven't tried it. I use the normal install from [postgresql.org](http://www.postgresql.org/download/).
1. Create a database named tradebindr or whatever you want. You may need to create a postgres user other than the default user or at least set a password for the default user. I forget.
1. `export DATABASE_URL=postgres://username:password@localhost:5432/database-name` to set a necessary environment variable tradebindr will need to start up. Replace username, password, and database-name of course.
1. Next we will create the database tables. In the future I'll use Alembic migrations so this will be easier.
1. `python` to start a repl
1. `from app import db` so we can work with the db
1. `db.create_all()` to populate the database with tables
1. `quit()` we're done there
1. You did it! Run the app with `python app.py`
1. You should be able to go to [http://localhost:5000](http://localhost:5000)
