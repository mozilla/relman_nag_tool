# all the imports
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

# configuration
DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'iphone'
USERNAME = 'admin'
PASSWORD = 'default'
APPLICATION_ROOT = 'https://b2gtestdrivers.allizom.org/relman_nag'