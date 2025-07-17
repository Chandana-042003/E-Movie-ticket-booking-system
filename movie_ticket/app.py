from flask import Flask, render_template, request, redirect, url_for
from bson import ObjectId
from pymongo import MongoClient

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["moviedb"]

# Initialize database with sample movies
def init_db():
    if db.movies.count_documents({}) == 0:
        movies = [
            {"name": "Avengers", "showtime": "7:00 PM", "available_seats": 50},
            {"name": "Inception", "showtime": "9:00 PM", "available_seats": 40},
            {"name": "Interstellar", "showtime": "6:00 PM", "available_seats": 30}
        ]
        db.movies.insert_many(movies)

@app.route('/')
def index():
    movies = list(db.movies.find())
    return render_template('index.html', movies=movies)

@app.route('/movie/<movie_id>')
def movie(movie_id):
    movie = db.movies.find_one({"_id": ObjectId(movie_id)})
    return render_template('movie.html', movie=movie)

@app.route('/book/<movie_id>', methods=['POST'])
def book(movie_id):
    username = request.form['username']
    seats = int(request.form['seats'])

    movie = db.movies.find_one({"_id": ObjectId(movie_id)})

    if not movie:
        return "Movie not found!", 404

    if seats > movie['available_seats']:
        return "Not enough seats available!"

    # Update seats
    db.movies.update_one(
        {"_id": ObjectId(movie_id)},
        {"$inc": {"available_seats": -seats}}
    )

    # Create booking
    db.bookings.insert_one({
        "username": username,
        "movie_id": ObjectId(movie_id),
        "seats": seats
    })

    return redirect(url_for('bookings'))

@app.route('/bookings')
def bookings():
    pipeline = [
        {
            "$lookup": {
                "from": "movies",
                "localField": "movie_id",
                "foreignField": "_id",
                "as": "movie_info"
            }
        }
    ]

    results = list(db.bookings.aggregate(pipeline))

    # Flatten movie name
    bookings = []
    for b in results:
        booking = {
            "_id": str(b["_id"]),
            "username": b["username"],
            "movie": b["movie_info"][0]["name"] if b["movie_info"] else "Unknown",
            "seats": b["seats"]
        }
        bookings.append(booking)

    return render_template('bookings.html', bookings=bookings)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
