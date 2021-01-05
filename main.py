from flask import Flask, render_template, redirect, url_for, request, flash, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from forms import OrderForm, AddProductForm, ChangeEventTitleForm
from sqlalchemy import JSON, func
from sqlalchemy.types import DateTime
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.ext.mutable import MutableDict
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import secrets
import sys
import json
import datetime
import uuid
import os
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['UPLOAD_PATH'] = 'uploads'
db = SQLAlchemy(app)
key = "[ebay-api-key]"
#Conversion to CAD
usdConvert = 1.3
productsfound = []

#Class to represent Orders table in database
class Orders(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	ordername = db.Column(db.String(120), unique=True, nullable=False)
	orderstatus = db.Column(db.String(20), nullable=False)
	trackinglink = db.Column(db.String(1000), nullable=False)
	ordernumber = db.Column(db.String(120), nullable=False, unique=True)
	products = db.relationship('Products', backref='order', lazy=True, cascade="all, delete-orphan")

	def __repr__(self):
		return f"Orders('{self.ordername}', '{self.orderstatus}','{self.trackinglink}', '{self.ordernumber}')"

#Class to represent Products table database
class Products(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	productname = db.Column(db.String(120), nullable=False)
	quantity = db.Column(db.Integer, nullable=False)
	ordernumber = db.Column(db.String(120), db.ForeignKey('orders.ordernumber'), nullable=False)

	def __repr__(self):
		return f"Product('{self.productname}', '{self.quantity}', '{self.ordernumber}')"

#Class to represent Events in calendar table database
class Events(db.Model):
	id = db.Column(db.String(60), primary_key = True)
	data = db.Column(MutableDict.as_mutable(db.JSON))

	def __repr__(self):
		return f"Events('{self.data}')"

#Default page will display orders in a table
@app.route("/")
@app.route("/index")
def home():
	order = Orders.query.all()
	return render_template('index.html', orders=order)

#Route to add new order from a from
@app.route("/add/new", methods=['GET', 'POST'])
def add_order():
	form = OrderForm()
	if form.validate_on_submit():
		order = Orders(ordername=form.ordername.data, ordernumber=form.ordernumber.data, orderstatus=form.orderstatus.data, trackinglink=form.trackinglink.data)
		db.session.add(order)
		db.session.commit()
		flash('Order added!', 'success')
		return redirect(url_for('home'))
	return render_template('add_order.html', title='Add Order', form=form, legend='Add Order')

#Route to view order individually
@app.route("/order/<int:order_id>")
def order(order_id):
	order = Orders.query.get_or_404(order_id)
	product = Products.query.filter(Products.ordernumber == order.ordernumber)
	return render_template('order.html', title=order.ordername, order=order, products=product)

#Route to edit selected order
@app.route("/order/<int:order_id>/edit", methods=['GET', 'POST'])
def order_edit(order_id):
	order = Orders.query.get_or_404(order_id)
    #Will reuse de same form as the form to add a new order
	form = OrderForm()
	if form.validate_on_submit():
		order.ordername = form.ordername.data
		order.ordernumber = form.ordernumber.data
		order.orderstatus = form.orderstatus.data
		order.trackinglink = form.trackinglink.data
		db.session.commit()
		flash('Order edited!', 'success')
		return redirect(url_for('order', order_id=order.id))
	elif request.method == 'GET':
		form.ordername.data = order.ordername
		form.orderstatus.data = order.orderstatus
		form.ordernumber.data = order.ordernumber
		form.trackinglink.data = order.trackinglink
	return render_template('add_order.html', title='Edit Order', form=form, legend='Edit Order')

#Route to delete an order
@app.route("/order/<int:order_id>/delete", methods=['GET', 'POST'])
def order_delete(order_id):
	order = Orders.query.get_or_404(order_id)
	db.session.delete(order)
	db.session.commit()
	flash('Order deleted!', 'success')
	return redirect(url_for('home'))

#Route to add a product in an order
@app.route("/order/<int:order_id>/addproduct", methods=['GET', 'POST'])
def add_product(order_id):
	order = Orders.query.get_or_404(order_id)
	form = AddProductForm()
	if form.validate_on_submit():
		for field in form.products:
			product = Products(productname=field.productname.data, quantity=field.quantity.data, ordernumber=order.ordernumber)
			db.session.add(product)
		db.session.commit()	
		flash('Product added!', 'success')
		return redirect(url_for('order', order_id=order.id))
	return render_template('add_product.html', form=form, title='Add Product', legend='Add Product', order_id=order.id)

#Route to edit a product in an order
@app.route("/product/<int:order_id>/<int:product_id>/editproduct", methods=['GET', 'POST'])
def product_edit(product_id, order_id):
	product = Products.query.get_or_404(product_id)
    #Will reuse de same form as the form to add a new product
	form = AddProductForm()
	if form.validate_on_submit():
		for field in form.products:
			product.productname = field.productname.data
			product.quantity = field.quantity.data
		db.session.commit()
		flash('Order edited!', 'success')
		return redirect(url_for('order', order_id=order_id))
	elif request.method == 'GET':
		for field in form.products:
			field.productname.data = product.productname
			field.quantity.data = product.quantity
	return render_template('add_product.html', form=form, title='Edit Product', legend='Edit Product', order_id=order_id)

#Route to delete an order
@app.route("/product/<int:order_id>/<int:product_id>/delete", methods=['GET', 'POST'])
def product_delete(product_id, order_id):
	product = Products.query.get_or_404(product_id)
	db.session.delete(product)
	db.session.commit()
	flash('Product deleted!', 'success')
	return redirect(url_for('order', order_id=order_id))

#Route to display calendar
@app.route("/calendar")
def calendar():
	return render_template('calendar.html', title='Calendar')

#Loading JSON data from the Events table in the database to display in calendar
@app.route("/load_data", methods=['GET', 'POST'])
def load_data():
    #Convert requested date to the same format as the date format in an Events object
	start_date = request.args.get('start', '')
	start_date = toDate(start_date.split("T")[0])
	end_date = request.args.get('end', '')
	end_date = toDate(end_date.split("T")[0])
	#Filter query results to be within the month
	event_data = Events.query.filter(Events.data['start'].as_string() >= start_date, Events.data['start'].as_string() <= end_date)
	eventlist = []
	for event in event_data:
		eventlist.append(event.data)
	return jsonify(eventlist)

#Route to save added event to the database
@app.route("/save_event_data", methods=['GET', 'POST'])
def save_event_data():
	sentdata = request.get_json()
	print(sentdata)
	start = toDate(sentdata['start'].split("T")[0])
	end = toDate(sentdata['end'].split("T")[0])
    #Using uuid to facilitate manipulation of events
	newID = uuid.uuid4()
	eventdata={
		"title": sentdata['title'],
		"start": str(start),
		"end": str(end),
		"allDay": sentdata['allDay'],
		"id" : str(newID),
	}
	print(eventdata)
	newevent = Events(id = str(newID), data=eventdata)
	db.session.add(newevent)
	db.session.commit()
	return render_template('calendar.html', title='Calendar')

#Route to update or delete event data
@app.route("/update_event_data", methods=['GET', 'POST'])
def update_event_data():
	if request.method == 'POST':
		sentdata = request.get_json()
		print(sentdata)
        #Modify event title if user doesn't leave title empty or click cancel
		if sentdata['title']:
			event = Events.query.get_or_404(sentdata['id'])
			event.data['title'] = sentdata['title']
			db.session.commit()
        #Delete event from database if user leave title empty or click cancel
		else:
			event = Events.query.get_or_404(sentdata['id'])
			db.session.delete(event)
			db.session.commit()
	return render_template('calendar.html', title='Calendar')

#Return uuid4
@app.route("/generate_id", methods=['GET', 'POST'])
def generate_id():
	return str(uuid.uuid4())

#Route to ebay search API page
@app.route("/ebay_search")
def ebay_search():
	return render_template('search.html')

#Route to file upload
@app.route("/upload_file", methods=['POST'])
def upload_file():
    uploaded_file = request.files['list']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        productsfound.clear()
        uploaded_file.save(uploaded_file.filename)
        output(filename)
    return redirect(url_for('search_result'))

#Route to display ebay search result
@app.route('/search_result')
def search_result():
    return("<p>" + "</p><p>".join(productsfound) + "</p>")

#Method to convert date
def toDate(dateString): 
	return datetime.datetime.strptime(dateString, "%Y-%m-%d").date()

#Method to call ebay search API using a file containing search terms
def output(filename):
    products = []
    with open(filename, "r") as searchfile:
        products = searchfile.readlines()
    for item in products:
        search = item.split(',')[0]
        MinPrice = item.split(',')[1]
        DistCost = item.split(',')[2]
        #Curreny used here is in CAD
        url = ('http://svcs.ebay.com/services/search/FindingService/v1\
?OPERATION-NAME=findItemsByKeywords\
&GLOBAL-ID=EBAY-ENCA\
&Currency=CAD\
&sortOrder=PricePlusShippingLowest\
&buyerPostalCode=[PostalCode]&SERVICE-VERSION=1.13.0\
&SECURITY-APPNAME=' + key +
'&RESPONSE-DATA-FORMAT=JSON\
&REST-PAYLOAD\
&itemFilter(0).name=Condition\
&itemFilter(0).value=1000\
&itemFilter(1).name=MinPrice\
&itemFilter(1).value=' + MinPrice+\
'&itemFilter(1).paramName=Currency\
&itemFilter(1).paramValue=CAD\
&itemFilter(2).name=ListingType\
&itemFilter(2).value=FixedPrice\
&paginationInput.entriesPerPage=5\
&keywords=' + search)
        url = url.replace(" ", "%20")
        #Request result and convert it to JSON
        apiResult = requests.get(url)
        parseddoc = apiResult.json()
        for item in (parseddoc["findItemsByKeywordsResponse"][0]["searchResult"][0]["item"]):
            title = item["title"][0]
            condition = item['condition'][0]['conditionDisplayName'][0]
            price = item['sellingStatus'][0]["convertedCurrentPrice"][0]['__value__']
            priceCost = float(DistCost) * usdConvert
            addproduct = title + " " + price + " " + str(priceCost) + " " + condition
            productsfound.append(addproduct)
            for item in productsfound:
                print(item)
    return redirect(url_for('search_result'))