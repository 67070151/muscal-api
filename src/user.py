from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date
from src.database import UserProfile, DailyFoodLog, db
from src.constants.http_status_code import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR

user = Blueprint("user", __name__, url_prefix="/muscal-api/user")

def calculate_progress(total, goal):
    """Helper function to calculate the progress percentage."""
    return (total / goal * 100) if goal > 0 else 0

@user.get('/dashboard')
@jwt_required()
def dashboard():
    """Retrieve user profile and daily progress for a specified date."""
    user_id = get_jwt_identity()

    log_date_str = request.args.get('log_date')
    try:
        log_date = date.fromisoformat(log_date_str) if log_date_str else date.today()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), HTTP_400_BAD_REQUEST

    # Retrieve user profile
    user_profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not user_profile:
        return jsonify({'error': 'User profile not found.'}), HTTP_404_NOT_FOUND

    # Retrieve daily log
    daily_log = DailyFoodLog.query.filter_by(user_id=user_id, log_date=log_date).first()
    
    # Calculate totals
    total_calories = daily_log.total_calories if daily_log else 0
    total_protein = daily_log.total_protein if daily_log else 0
    total_carbohydrates = daily_log.total_carbohydrates if daily_log else 0
    total_fat = daily_log.total_fat if daily_log else 0

    # Calculate goal values
    calorie_goal = user_profile.calorie_goal
    protein_goal = ((user_profile.protein_goal / 100) * calorie_goal) / 4
    carbohydrate_goal = ((user_profile.carbohydrate_goal / 100) * calorie_goal) / 4
    fat_goal = ((user_profile.fat_goal / 100) * calorie_goal) / 9

    formatted_log_date = log_date.strftime("%d-%m-%Y")

    response = {
        'user_id': user_profile.user_id,
        'log_date': formatted_log_date,
        'goal': {
            'calorie_goal': calorie_goal,
            'protein_goal': protein_goal,
            'carbohydrate_goal': carbohydrate_goal,
            'fat_goal': fat_goal,
        },
        'total': {
            'total_calories': total_calories,
            'total_protein': total_protein,
            'total_carbohydrates': total_carbohydrates,
            'total_fat': total_fat,
        },
        'progress': {
            'calorie_progress': calculate_progress(total_calories, calorie_goal),
            'protein_progress': calculate_progress(total_protein, protein_goal),
            'carbohydrate_progress': calculate_progress(total_carbohydrates, carbohydrate_goal),
            'fat_progress': calculate_progress(total_fat, fat_goal),
        }
    }

    return jsonify(response), HTTP_200_OK

@user.post('/set_goal')
@jwt_required()
def set_goal():
    """Endpoint to set user dietary goals, ensuring protein, carb, and fat goals sum to 100 or less."""
    user_id = get_jwt_identity()
    request_data = request.json

    # Retrieve user profile
    user_profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not user_profile:
        return jsonify({'error': 'User profile not found.'}), HTTP_404_NOT_FOUND

    # Extract and set dietary goals with defaults
    calorie_goal = request_data.get('calorie_goal', user_profile.calorie_goal)
    protein_goal = request_data.get('protein_goal', user_profile.protein_goal)
    carbohydrate_goal = request_data.get('carbohydrate_goal', user_profile.carbohydrate_goal)
    fat_goal = request_data.get('fat_goal', user_profile.fat_goal)

    # Check that the sum of protein, carbs, and fats does not equal 100
    if protein_goal + carbohydrate_goal + fat_goal != 100:
        return jsonify({'error': 'Sum of protein, carbohydrate, and fat goals not equal 100.'}), HTTP_400_BAD_REQUEST

    # Update goals if valid
    user_profile.calorie_goal = calorie_goal
    user_profile.protein_goal = protein_goal
    user_profile.carbohydrate_goal = carbohydrate_goal
    user_profile.fat_goal = fat_goal

    try:
        db.session.commit()
        return jsonify({
            'message': 'Goals updated successfully.',
            'goal':{
                'calorie_goal': user_profile.calorie_goal,
                'protein_goal': user_profile.protein_goal,
                'carbohydrate_goal': user_profile.carbohydrate_goal,
                'fat_goal': user_profile.fat_goal
            }
            }), HTTP_200_OK
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), HTTP_500_INTERNAL_SERVER_ERROR
