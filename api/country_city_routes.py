from flask import request, abort
from flask_restx import Namespace, Resource, fields
from models.country import Country
from models.city import City

ns_countries = Namespace('countries', description='Country operations')
ns_cities = Namespace('cities', description='City operations')

# Define the model for a Country
country_model = ns_countries.model('Country', {
    'name': fields.String(required=True, description='The name of the country'),
    'code': fields.String(required=True, description='The ISO 3166-1 alpha-2 code of the country'),
    'created_at': fields.DateTime(readOnly=True, description='The date and time the country was created'),
    'updated_at': fields.DateTime(readOnly=True, description='The date and time the country was last updated'),
    'cities': fields.List(fields.Nested(ns_cities.model('City', {
        'id': fields.String(readOnly=True, description='The unique identifier of a city'),
        'name': fields.String(required=True, description='The name of the city'),
        'country_code': fields.String(required=True, description='The ISO 3166-1 alpha-2 code of the country the city belongs to'),
        'created_at': fields.DateTime(readOnly=True, description='The date and time the city was created'),
        'updated_at': fields.DateTime(readOnly=True, description='The date and time the city was last updated')
    })))
})

# Define the model for a City
city_model = ns_cities.model('City', {
    'id': fields.String(readOnly=True, description='The unique identifier of a city'),
    'name': fields.String(required=True, description='The name of the city'),
    'country_code': fields.String(required=True, description='The ISO 3166-1 alpha-2 code of the country the city belongs to'),
    'created_at': fields.DateTime(readOnly=True, description='The date and time the city was created'),
    'updated_at': fields.DateTime(readOnly=True, description='The date and time the city was last updated')
})

@ns_countries.route('/')
class CountryList(Resource):
    """
    Resource for getting a list of all Countries and creating new Countries.
    """
    @ns_countries.doc('list_countries')
    @ns_countries.marshal_list_with(country_model)
    def get(self):
        """Return a list of all Countries."""
        countries = Country.load_all()
        return [country.to_dict() for country in countries] 

    @ns_countries.doc('create_country')
    @ns_countries.expect(country_model)
    @ns_countries.marshal_with(country_model, code=201)
    def post(self):
        """Create a new Country."""
        if not request.json: # Check if the request payload is JSON
            abort(400, description="Request payload must be JSON")
        data = request.json
        try:
            # Create a new Country object from the request data
            country = Country(
                name=data['name'],
                code=data['code']
            )
        except ValueError as e:
            abort(400, description=str(e))
        return country.to_dict(), 201

@ns_countries.route('/<string:country_code>')
class CountryResource(Resource):
    """
    Resource for getting, updating, and deleting individual Countries.
    """
    @ns_countries.doc('get_country')
    @ns_countries.marshal_with(country_model)
    def get(self, country_code):
        """Return the Country with the given code."""
        country = next((c for c in Country.load_all() if c.code == country_code), None)
        if not country:
            return {'message': 'Country not found'}, 404
        return country.to_dict()

@ns_countries.route('/<string:country_code>/cities')
class CountryCityList(Resource):
    """
    Resource for getting a list of all Cities for a given Country.
    """
    @ns_countries.doc('list_cities_for_country')
    @ns_countries.marshal_list_with(city_model)
    def get(self, country_code):
        """Return a list of all Cities for the given Country code."""
        country = next((c for c in Country.load_all() if c.code == country_code), None)
        if not country:
            return {'message': 'Country not found'}, 404
        return [city.to_dict() for city in country.cities]

@ns_cities.route('/')
class CityList(Resource):
    """
    Resource for getting a list of all Cities and creating new Cities.
    """
    @ns_cities.doc('list_cities')
    @ns_cities.marshal_list_with(city_model)
    def get(self):
        """Return a list of all Cities."""
        cities = City.load_all()
        return [city.to_dict() for city in cities]

    @ns_cities.doc('create_city')
    @ns_cities.expect(city_model)
    @ns_cities.marshal_with(city_model, code=201)
    def post(self):
        """Create a new City."""
        if not request.json:
            abort(400, description="Request payload must be JSON")
        data = request.json
        country = next((c for c in Country.load_all() if c.code == data['country_code']), None)
        if not country:
            abort(404, description="Country not found")
        city = City(
            name=data['name'],
            country_code=country.code
        )
        country.add_city(city)
        return city.to_dict(), 201

@ns_cities.route('/<string:city_id>')
class CityResource(Resource):
    """
    Resource for getting, updating, and deleting individual Cities.
    """
    @ns_cities.doc('get_city')
    @ns_cities.marshal_with(city_model)
    def get(self, city_id):
        """Return the City with the given ID."""
        city = City.load(city_id)
        if not city:
            return {'message': 'City not found'}, 404
        return city.to_dict()

    @ns_cities.doc('update_city')
    @ns_cities.expect(city_model)
    @ns_cities.marshal_with(city_model)
    def put(self, city_id):
        """Update the City with the given ID."""
        if not request.json:
            abort(400, description="Request payload must be JSON")
        data = request.json
        city = City.load(city_id)
        if not city:
            abort(404, description="City not found")
        city.name = data.get('name', city.name)
        city.save()
        return city.to_dict()

    @ns_cities.doc('delete_city')
    @ns_cities.response(204, 'City deleted')
    def delete(self, city_id):
        """Delete the City with the given ID."""
        city = City.load(city_id)
        if not city:
            return {'message': 'City not found'}, 404
        City.delete(city_id)
        return '', 204
