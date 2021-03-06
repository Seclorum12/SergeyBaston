import random

from http import HTTPStatus

from webargs import fields, validate
from webargs.flaskparser import use_kwargs
from flask import Flask, request, jsonify

from helpers.helpers import password_generator, get_statistic_from_csv, persons_generator, object_to_csv, object_to_str, \
	get_bitcoin_value, buy_btc
from const import const

app = Flask(__name__)


@app.errorhandler(HTTPStatus.UNPROCESSABLE_ENTITY)
@app.errorhandler(HTTPStatus.BAD_REQUEST)
def error_handler(error):
	"""
	Error processing
	:param error:
	:return: object
	"""
	headers = error.data.get('headers', None)
	messages = error.data.get('messages', ['incorrect request'])
	if headers:
		return jsonify({'errors': messages}, headers, error.code)
	else:
		return jsonify({'errors': messages}, error.code)


@app.route('/')
def index_page() -> str:
	"""
	Entry point for route /
	(Index page)
	:return:
	"""
	return '<p> /password - generated password</p><p>/statistic - work from CSV file</p>\
	<p>/students?amount=3&country=EN&file=Student - list students (store to csv)</p>\
	<p>/bitcoin_rate?currency=USD&change=100 - course and exchange BTC</p>'


@app.route('/password')
def generate_password() -> str:
	"""
	Entry point for route /pass
	(Generating password)
	:return: string
	"""
	len_password = random.randint(10, 20)
	password = password_generator(len_password)  # use clean function for generated password
	return f'<p>Password long: {len_password}</p>Password: {password}'


@app.route('/statistic')
def average_statistic():
	"""
	Entry point for route /statistic
	(Reading from csv and calculating average)
	:return: string
	"""
	statistic = get_statistic_from_csv(const.CSV_NAME)
	return f"<p>All records in files: {statistic['len']}</p><p>Average Height(Inches): {statistic['avg_height']}</p>\
	<p>Average Weight(Pounds): {statistic['avg_weight']}</p>"


@app.route('/students')
@use_kwargs(
	{
		'amount': fields.Int(missing=1, validate=[validate.Range(min=1, max=1000)]),
		'country': fields.Str(missing='UK', validate=[validate.Length(2)]),
		'file': fields.Str(required=True, validate=[validate.Length(max=12), validate.Regexp('^\w+$')])
	},
	location='query'
)
def generate_students(amount: int, country: str, file: str):
	"""
	Entry point for /students with parameters
	(Adding functionality generating students, save data to file and  output on client by formatted HTML string)
	:param amount:
	:param country:
	:param file:
	:return:
	"""
	students = persons_generator(amount=amount, country_code=country)
	object_to_csv(students, file)
	out_string = object_to_str(students)
	return out_string


@app.route('/bitcoin_rate')
@use_kwargs(
	{
		'currency': fields.Str(missing='USD', validate=[validate.Length(max=4)]),
		'change': fields.Int(missing=None)
	},
	location='query'
)
def bitcoin_exchange(currency: str, change: int):
	"""
	Entry point for /bitcoin_rate with parameters
	(Get bitcoin rate and exchange calculation user currency to BTC)
	:param currency: currency code (ex. USD, EUR)
	:param change: integer how money exchange
	:return: string
	"""
	bitcoin_rate_dict = get_bitcoin_value(currency)
	if not bitcoin_rate_dict:
		return f"Error connection to {const.BTC_RATE_API}"
	elif 'error' in bitcoin_rate_dict:
		return f"Error: {bitcoin_rate_dict['error']}"
	if change:
		exchange_finally_sum = buy_btc(rate_dict=bitcoin_rate_dict, summ=change)
	return f'<p>Exchange rate:<br> 1 BTC = {bitcoin_rate_dict["symbol"]}{bitcoin_rate_dict["rate"]}  [{currency}]</p>\
	<p>{str(f"Exchange: {change} {currency} = {exchange_finally_sum} BTC") if change else str("For exchange use parameter change=100")}</p>'


if __name__ == '__main__':
	app.run(host="127.0.0.1", port=5000, debug=True)
