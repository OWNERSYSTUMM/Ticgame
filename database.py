from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users = db["users"]


def get_user(user_id, name):
    if not users.find_one({"user_id": user_id}):
        users.insert_one({
            "user_id": user_id,
            "name": name,
            "coins": 100,
            "wins": 0,
            "losses": 0,
            "draws": 0
        })


def add_win(user_id):
    users.update_one(
        {"user_id": user_id},
        {"$inc": {"wins": 1, "coins": 20}}
    )


def add_loss(user_id):
    users.update_one(
        {"user_id": user_id},
        {"$inc": {"losses": 1, "coins": -10}}
    )


def add_draw(user_id):
    users.update_one(
        {"user_id": user_id},
        {"$inc": {"draws": 1}}
    )


def get_leaderboard():
    return list(
        users.find({}, {"_id": 0})
        .sort("wins", -1)
        .limit(10)
    )
