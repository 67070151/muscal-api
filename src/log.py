from src.constants.http_status_code import *
from flask import Blueprint, request, jsonify
from src.database import db, FoodItem, DailyFoodLog, FoodLogEntry
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date, datetime

log = Blueprint("log", __name__, url_prefix="/muscal-api/log")

@log.get('/view_log/', defaults={'log_date': None})
@log.get('/view_log/<log_date>')
@jwt_required()
def view_log(log_date):
    """Endpoint to view food log and daily totals for a specific day."""
    user_id = get_jwt_identity()

    # If log_date is provided, parse it; otherwise, use today's date
    if log_date:
        try:
            log_date = datetime.strptime(log_date, '%d-%m-%Y').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use dd-mm-yyyy.'}), HTTP_400_BAD_REQUEST
    else:
        log_date = date.today()

    # Retrieve the daily log for the specified or default date
    daily_log = DailyFoodLog.query.filter_by(user_id=user_id, log_date=log_date).first()
    if not daily_log:
        return jsonify({'message': 'No log found for this date.'}), HTTP_404_NOT_FOUND

    entries = []
    for entry in daily_log.food_entries:
        food_item = FoodItem.query.get(entry.food_id)
        entries.append({
            'entry_id': entry.entry_id,
            'food_name': food_item.food_name,
            'quantity': entry.quantity,
            'nutritions': {
                'calories': food_item.calories_per_serving * entry.quantity,
                'protein': food_item.protein_per_serving * entry.quantity,
                'carbohydrates': food_item.carbohydrates_per_serving * entry.quantity,
                'fat': food_item.fat_per_serving * entry.quantity
            }
        })

    return jsonify({
        'date': log_date.strftime('%d-%m-%Y'),
        'total_calories': daily_log.total_calories,
        'total_protein': daily_log.total_protein,
        'total_carbohydrates': daily_log.total_carbohydrates,
        'total_fat': daily_log.total_fat,
        'entries': entries
    }), HTTP_200_OK


@log.post('/log_food')
@jwt_required()
def log_food():
    """Endpoint to log food entries for a specific day and update daily totals."""
    user_id = get_jwt_identity()

    log_date = request.json.get('log_date', date.today())
    if isinstance(log_date, str):
        try:
            log_date = datetime.strptime(log_date, '%d-%m-%Y').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use dd-mm-yyyy.'}), HTTP_400_BAD_REQUEST

    food_id = request.json.get('food_id')
    quantity = request.json.get('quantity')

    if not food_id or not quantity:
        return jsonify({'error': 'food_id and quantity are required.'}), HTTP_400_BAD_REQUEST

    daily_log = DailyFoodLog.query.filter_by(user_id=user_id, log_date=log_date).first()
    if not daily_log:
        daily_log = DailyFoodLog(user_id=user_id, log_date=log_date)
        db.session.add(daily_log)
        db.session.commit()

    food_item = FoodItem.query.get(food_id)
    if not food_item:
        return jsonify({'error': 'Food item not found.'}), HTTP_404_NOT_FOUND

    food_log_entry = FoodLogEntry(log_id=daily_log.log_id, food_id=food_item.food_id, quantity=quantity)
    db.session.add(food_log_entry)

    daily_log.total_calories += food_item.calories_per_serving * quantity
    daily_log.total_protein += food_item.protein_per_serving * quantity
    daily_log.total_carbohydrates += food_item.carbohydrates_per_serving * quantity
    daily_log.total_fat += food_item.fat_per_serving * quantity

    try:
        db.session.commit()
        return jsonify({'message': 'Food logged successfully and totals updated.'}), HTTP_201_CREATED
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), HTTP_500_INTERNAL_SERVER_ERROR

@log.delete('/delete_food_entry/<int:entry_id>')
@jwt_required()
def delete_food_entry(entry_id):
    """Endpoint to delete a specific food log entry and update daily totals."""
    user_id = get_jwt_identity()

    # Find the food log entry by entry_id
    food_log_entry = FoodLogEntry.query.filter_by(entry_id=entry_id).first()
    if not food_log_entry:
        return jsonify({'error': 'Food log entry not found.'}), HTTP_404_NOT_FOUND

    # Retrieve the associated daily log and verify user ownership
    daily_log = DailyFoodLog.query.get(food_log_entry.log_id)
    if daily_log.user_id != user_id:
        return jsonify({'error': 'Unauthorized to delete this entry.'}), HTTP_403_FORBIDDEN

    # Retrieve the associated food item and adjust daily totals
    food_item = FoodItem.query.get(food_log_entry.food_id)
    quantity = food_log_entry.quantity

    # Update daily totals before deletion
    daily_log.total_calories -= food_item.calories_per_serving * quantity
    daily_log.total_protein -= food_item.protein_per_serving * quantity
    daily_log.total_carbohydrates -= food_item.carbohydrates_per_serving * quantity
    daily_log.total_fat -= food_item.fat_per_serving * quantity

    # Delete the entry and commit changes
    db.session.delete(food_log_entry)
    try:
        db.session.commit()
        return jsonify({'message': 'Food log entry deleted and totals updated.'}), HTTP_200_OK
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), HTTP_500_INTERNAL_SERVER_ERROR
