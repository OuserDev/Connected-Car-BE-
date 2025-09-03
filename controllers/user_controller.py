from flask import Blueprint, jsonify
from models.user import UserModel

user_bp = Blueprint('user', __name__)
user_model = UserModel()