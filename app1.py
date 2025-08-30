from flask import Flask, render_template, redirect, url_for, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import json
import requests

app = Flask(__name__)

# --------------------
# Database configuration
# --------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --------------------
# Database Models
# --------------------
class Pet(db.Model):
    type = db.Column(db.String(20))
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.String(20)) 
    gender = db.Column(db.String(10))
    size = db.Column(db.String(50)) 
    breed = db.Column(db.String(100))

    image_url = db.Column(db.String(200))
    description = db.Column(db.Text)

    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(50))
    contact_city = db.Column(db.String(100))
    contact_state = db.Column(db.String(100))

class HeartedPet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'))
    pet = db.relationship('Pet')

class SkippedPet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'))
    pet = db.relationship('Pet')

# --------------------
# Load pets from JSON (only once for testing)
# --------------------
def load_sample_pets():
    if not Pet.query.first():  # load only if DB is empty
        with open('pets.json') as f:
            pets = json.load(f)
        for pet in pets:
            new_pet = Pet(name=pet['name'], 
                          image_url=pet['image_url'], 
                          description=pet['description'])
            db.session.add(new_pet)
        db.session.commit()

# --------------------
# Petfinder API intergration
# --------------------

# fetch access token from Petfinder API
def get_access_token(api_key, api_secret):
    url = "https://api.petfinder.com/v2/oauth2/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": api_secret,
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()['access_token']

# fetch pets by type and location using thr access token
def fetch_pets(access_token, location="10001", limit=10, pet_type="dog"):
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "location": location,
        "limit": limit,
        "type": pet_type,
    }
    response = requests.get("https://api.petfinder.com/v2/animals", headers=headers, params=params)
    response.raise_for_status()
    return response.json()['animals']

# load pets from API into local database
def load_pets_from_api():
    api_key = "ENTER-KEY-HERE"
    api_secret = "ENTER-SECRET-HERE"
    #api_key = os.environ.get("PETFINDER_API_KEY")
    #api_secret = os.environ.get("PETFINDER_API_SECRET")
    token = get_access_token(api_key, api_secret)
    
    all_types = ["dog", "cat"]
    
    pets = fetch_pets(token)
    for pet_type in all_types:
        pets = fetch_pets(token, pet_type=pet_type)
        for pet in pets:
            new_pet = Pet(
                type=pet.get('type', 'Unknown'),
                name=pet['name'],
                age=pet.get('age', ''),
                gender=pet.get('gender', ''),
                size=pet.get('size', ''),
                breed=pet.get('breeds', {}).get('primary', 'Unknown'),
                image_url=pet['photos'][0]['medium'] if pet['photos'] else '',
                description=pet.get('description') or 'No description available.',
                contact_email=pet.get('contact', {}).get('email'),
                contact_phone=pet.get('contact', {}).get('phone'),
                contact_city=pet.get('contact', {}).get('address', {}).get('city'),
                contact_state=pet.get('contact', {}).get('address', {}).get('state'),
            )
            db.session.add(new_pet)
    db.session.commit()

# --------------------
# Routes
# --------------------

#for home page
@app.route('/')
def index():
    # get a pet that hasn’t been hearted or skipped yet
    hearted_ids = [a.pet_id for a in HeartedPet.query.all()]
    skipped_ids = [s.pet_id for s in SkippedPet.query.all()]
    excluded_ids = hearted_ids + skipped_ids
    pet = Pet.query.filter(~Pet.id.in_(excluded_ids)).order_by(db.func.random()).first()
    return render_template('index.html', pet=pet)

@app.route('/hearted')
def hearted():
    # show all liked pets
    hearted_pets = [entry.pet for entry in HeartedPet.query.all()]
    return render_template('hearted.html', hearted_pets=hearted_pets)

@app.route('/previous')
def previous():
    # show all skipped pets
    skipped_pets = [entry.pet for entry in SkippedPet.query.all()]
    return render_template('previous.html', skipped_pets=skipped_pets)

@app.route('/filter')
def filter():
    return render_template('filter.html')

@app.route('/adopt/<int:pet_id>', methods= ['POST'])
def adopt(pet_id):
    # remove from skipped if it exists
    skipped_entry = SkippedPet.query.filter_by(pet_id=pet_id).first()
    if skipped_entry:
        db.session.delete(skipped_entry)

    # add to hearted if not already
    if not HeartedPet.query.filter_by(pet_id=pet_id).first():
        hearted = HeartedPet(pet_id=pet_id)
        db.session.add(hearted)

    db.session.commit()
    # handles AJAX or regular redirect
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success'})
    else:
        return redirect(url_for('previous'))

@app.route('/skip/<int:pet_id>', methods= ['POST'])
def skip(pet_id):
    # remove from hearted if it exists
    hearted_entry = HeartedPet.query.filter_by(pet_id=pet_id).first()
    if hearted_entry:
        db.session.delete(hearted_entry)

    # add to skipped if not already
    if not SkippedPet.query.filter_by(pet_id=pet_id).first():
        skipped = SkippedPet(pet_id=pet_id)
        db.session.add(skipped)

    db.session.commit()
    # handles AJAX or regular redirect
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'success'})
    else:
        return redirect(url_for('hearted'))
    
@app.route('/filter-results', methods=['GET'])
def filter_results():
    #get filters from form
    pet_type = request.args.get('pet_type')
    gender = request.args.get('gender')
    city = request.args.get('city')
    state = request.args.get('state')
    query = Pet.query

    # filter by type
    if pet_type and pet_type != 'Either':
        query = query.filter(Pet.type == pet_type)

    # filter by gender
    if gender and gender != 'Either':
        query = query.filter(Pet.gender == gender)

    # filter by state/location (case insenitive)
    if city:
        query = query.filter(Pet.contact_city.ilike(f"%{city.strip()}%"))
    if state:
        query = query.filter(Pet.contact_state.ilike(f"%{state.strip()}%"))

    pets = query.all()
    return render_template('filtered_results.html', pets=pets)

    
@app.route('/pet/<int:pet_id>')
def pet_details(pet_id):
    # show full detials for a single pet
    pet = Pet.query.get_or_404(pet_id)
    return render_template('details.html', pet=pet)

@app.route('/next-pet')
def next_pet():
    # API endpoint for getting the next pet via AJAX
    hearted_ids = [a.pet_id for a in HeartedPet.query.all()]
    skipped_ids = [s.pet_id for s in SkippedPet.query.all()]
    excluded_ids = hearted_ids + skipped_ids
    pet = Pet.query.filter(~Pet.id.in_(excluded_ids)).order_by(db.func.random()).first()
    if pet:
        return jsonify({
            'id': pet.id,
            'name': pet.name,
            'breed' : pet.breed,
            'gender' : pet.gender,
            'age' : pet.age,
            'size' : pet.size,
            'image_url': pet.image_url,
            'description': pet.description
        })
    else:
        return jsonify({'no_more': True})

# --------------------
# Run the app
# --------------------

if __name__ == '__main__':
    with app.app_context():
        # create tables first
        db.create_all()

        # clear existing data (only during development)
        db.session.query(HeartedPet).delete()
        db.session.query(SkippedPet).delete()
        db.session.query(Pet).delete()
        db.session.commit()

        # load pets from API
        load_pets_from_api()   #load_sample_pets() testing only   

    app.run(debug=True)
