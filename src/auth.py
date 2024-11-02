from src.constants.http_status_code import *
from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from src.database import *
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity

auth = Blueprint("auth", __name__, url_prefix="/muscal-api/auth")

@auth.post('/register')
def register():
    username = request.json.get('username')
    password = request.json.get('password')

    # Validate password length
    if len(password) < 4:
        return jsonify({'error': "Password is too short"}), HTTP_400_BAD_REQUEST

    # Validate username length and format
    if len(username) < 3:
        return jsonify({'error': "Username is too short"}), HTTP_400_BAD_REQUEST
    if not username.isalnum() or " " in username:
        return jsonify({'error': "Username should be alphanumeric and have no spaces"}), HTTP_400_BAD_REQUEST

    # Check if the email or username is already taken
    if UserLogin.query.filter_by(username=username).first() is not None:
        return jsonify({'error': "Username is taken"}), HTTP_409_CONFLICT

    # Hash the password and create a new user
    password_hash = generate_password_hash(password)
    user = UserLogin(username=username, password_hash=password_hash)
    db.session.add(user)
    db.session.commit()

    new_user_profile = UserProfile(user_id=user.user_id)
    db.session.add(new_user_profile)
    db.session.commit()

    return jsonify({
        'message': "User created",
        'user': {
            'username': username,
        }
    }), HTTP_201_CREATED

@auth.post('/login')
def login():
    username = request.json.get('username', '')
    password = request.json.get('password', '')

    user = UserLogin.query.filter_by(username=username).first()

    if user:
        is_pass_correct = check_password_hash(user.password_hash, password)

        if is_pass_correct:
            refresh = create_refresh_token(identity=user.user_id)
            access = create_access_token(identity=user.user_id)

            return jsonify({
                'user': {
                    'refresh': refresh,
                    'access': access,
                    'username': user.username,
                }
            }), HTTP_200_OK

    return jsonify({'error': 'Wrong credentials'}), HTTP_401_UNAUTHORIZED

@auth.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Endpoint to log out the user."""
    # Invalidate the JWT on the client-side (e.g., remove it from local storage)
    return jsonify({'message': 'Logged out successfully.'}), 200

@auth.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = UserLogin.query.filter_by(id=user_id).first()
    return jsonify({
        "username": user.username,
        }), HTTP_200_OK

@auth.get('/token/refresh')
@jwt_required(refresh=True)
def refresh_users_token():
    identity = get_jwt_identity()
    access = create_access_token(identity=identity)

    return jsonify({
        'access': access
    }), HTTP_200_OK
