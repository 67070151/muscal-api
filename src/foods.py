from src.constants.http_status_code import *
from flask import Blueprint, request, jsonify
from src.database import *
from flask_jwt_extended import jwt_required

foods = Blueprint("foods", __name__, url_prefix="/muscal-api/foods")

@foods.get('/view_all_food')
@jwt_required()
def view_all_food():
    """Endpoint to view all food items."""

    food_items = FoodItem.query.all()
    if not food_items:
        return jsonify({'message': 'No food items found.'}), HTTP_404_NOT_FOUND

    food_list = [{
        'food_id': item.food_id,
        'food_name': item.food_name,
        'serving': {
            'serving_size': item.serving_size,
            'servings_per_container': item.servings_per_container
        },
        'nutritions': {
            'calories_per_serving': item.calories_per_serving,
            'carbohydrates_per_serving': item.carbohydrates_per_serving,
            'protein_per_serving': item.protein_per_serving,
            'fat_per_serving': item.fat_per_serving
        }
    } for item in food_items]

    return jsonify({'food_items': food_list}), HTTP_200_OK

@foods.post('/add_food')
@jwt_required()
def add_food():
    """Endpoint to add a food item to the database."""

    request_data = request.json
    food_name = request_data.get('food_name')
    serving_size = request_data.get('serving_size')
    servings_per_container = request_data.get('servings_per_container')
    calories_per_serving = request_data.get('calories_per_serving')

    # Get optional fields, allowing for 0 inputs
    carbohydrates_per_serving = request_data.get('carbohydrates_per_serving', 0)
    protein_per_serving = request_data.get('protein_per_serving', 0)
    fat_per_serving = request_data.get('fat_per_serving', 0)

    # Validate required fields
    if not all([food_name, serving_size, servings_per_container, calories_per_serving]):
        return jsonify({'error': 'Food name, serving size, servings per container, and calories per serving are required.'}), HTTP_400_BAD_REQUEST

    # Convert to integers, ensuring they are numerical
    try:
        servings_per_container = int(servings_per_container)
        calories_per_serving = int(calories_per_serving)
        carbohydrates_per_serving = int(carbohydrates_per_serving)
        protein_per_serving = int(protein_per_serving)
        fat_per_serving = int(fat_per_serving)
    except ValueError:
        return jsonify({'error': 'All numeric fields must be valid numbers.'}), HTTP_400_BAD_REQUEST

    new_food = FoodItem(
        food_name=food_name,
        serving_size=serving_size,
        servings_per_container=servings_per_container,
        calories_per_serving=calories_per_serving,
        carbohydrates_per_serving=carbohydrates_per_serving,
        protein_per_serving=protein_per_serving,
        fat_per_serving=fat_per_serving
    )

    try:
        db.session.add(new_food)
        db.session.commit()
        return jsonify({
            'message': 'Food item added successfully.',
            'food': {
                "food_name": food_name,
                "serving_size": serving_size,
                "servings_per_container": servings_per_container,
                "calories_per_serving": calories_per_serving,
                "carbohydrates_per_serving": carbohydrates_per_serving,
                "protein_per_serving": protein_per_serving,
                "fat_per_serving": fat_per_serving
            }
        }), HTTP_201_CREATED
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error adding food item: {str(e)}'}), HTTP_500_INTERNAL_SERVER_ERROR

@foods.delete('/delete_food/<int:food_id>')
@jwt_required()
def delete_food(food_id):
    """Endpoint to delete a food item, ensuring related food log entries are also deleted."""

    food_item = FoodItem.query.filter_by(food_id=food_id).first()

    if not food_item:
        return jsonify({'error': 'Food item not found.'}), HTTP_404_NOT_FOUND

    try:
        FoodLogEntry.query.filter_by(food_id=food_id).delete()
        db.session.delete(food_item)
        db.session.commit()
        return jsonify({'message': 'Food item and related log entries deleted successfully.'}), HTTP_200_OK

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error deleting food item: {str(e)}'}), HTTP_500_INTERNAL_SERVER_ERROR
