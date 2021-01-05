from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, IntegerField, FieldList, FormField
from wtforms.fields import html5 as h5fields
from wtforms.widgets import html5 as h5widgets
from wtforms.validators import DataRequired, ValidationError

class ProductForm(FlaskForm):
	productname = StringField('Product Name')
	quantity = IntegerField('Quantity', widget=h5widgets.NumberInput(min=0, step=1))

class OrderForm(FlaskForm):
    ordername = StringField('Name', validators=[DataRequired()])
    orderstatus = StringField('Order Status', validators=[DataRequired()])
    trackinglink = TextAreaField('Tracking link', validators=[DataRequired()])
    ordernumber = StringField('Order Number', validators=[DataRequired()])
    submit = SubmitField('Submit')

class AddProductForm(FlaskForm):
	products = FieldList(FormField(ProductForm), min_entries=1, max_entries=None)
	submit = SubmitField('Submit')

class ChangeEventTitleForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired()])
	submit = SubmitField('Submit')