from flask import request, jsonify
from src.application.services.user_service import UserService


class UserController:
    """Controller for user endpoints"""

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    def create_user(self):
        """Create a new user"""
        try:
            data = request.get_json()

            if not data:
                return jsonify({
                    'error': 'Request body is required',
                    'message': 'Please provide a valid JSON request body'
                }), 400

            # Required fields
            required_fields = ['phone_number']
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                return jsonify({
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields
                }), 400

            # Handle agent_id - support both single value and array
            agent_id = data.get('agent_id') or data.get('agentId')
            if agent_id:
                if isinstance(agent_id, list):
                    data['agent_ids'] = agent_id
                else:
                    data['agent_ids'] = [agent_id]
                data.pop('agent_id', None)
                data.pop('agentId', None)

            # Apply defaults for language and validity_days
            if 'language' not in data and 'language' not in data:
                data['language'] = 'es'
            if 'validity_days' not in data and 'validityDays' not in data:
                data['validity_days'] = 30
            elif 'validityDays' in data:
                data['validity_days'] = data.pop('validityDays')

            # Check if user exists to determine response message
            existing_user = self.user_service.get_user_by_phone(data.get('phone_number'))
            
            # Create user (or assign to agent if exists)
            user = self.user_service.create_user(data)

            response_data = self.user_service._to_response_dict(user)

            if existing_user:
                return jsonify({
                    'message': 'User already exists, assigned to agent',
                    'data': response_data
                }), 200
            else:
                return jsonify({
                    'message': 'User created successfully',
                    'data': response_data
                }), 201

        except ValueError as e:
            return jsonify({
                'error': 'Validation error',
                'message': str(e)
            }), 400
        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500

    def get_user(self, user_id):
        """Get a user by ID"""
        try:
            user_data = self.user_service.get_user_by_id(int(user_id))

            if not user_data:
                return jsonify({
                    'error': 'Not found',
                    'message': f'User with ID {user_id} not found'
                }), 404

            return jsonify({
                'message': 'User retrieved successfully',
                'data': user_data
            }), 200

        except ValueError as e:
            return jsonify({
                'error': 'Bad request',
                'message': str(e)
            }), 400
        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500

    def get_user_by_phone(self, phone_number):
        """Get a user by phone number"""
        try:
            user_data = self.user_service.get_user_by_phone(phone_number)

            if not user_data:
                return jsonify({
                    'error': 'Not found',
                    'message': f'User with phone number {phone_number} not found'
                }), 404

            return jsonify({
                'message': 'User retrieved successfully',
                'data': user_data
            }), 200

        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500

    def update_user(self, user_id):
        """Update a user"""
        try:
            data = request.get_json()

            if not data:
                return jsonify({
                    'error': 'Request body is required',
                    'message': 'Please provide a valid JSON request body'
                }), 400

            user = self.user_service.update_user(int(user_id), data)

            if not user:
                return jsonify({
                    'error': 'Not found',
                    'message': f'User with ID {user_id} not found'
                }), 404

            response_data = self.user_service._to_response_dict(user)

            return jsonify({
                'message': 'User updated successfully',
                'data': response_data
            }), 200

        except ValueError as e:
            return jsonify({
                'error': 'Validation error',
                'message': str(e)
            }), 400
        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500

    def delete_user(self, user_id):
        """Delete a user"""
        try:
            success = self.user_service.delete_user(int(user_id))

            if not success:
                return jsonify({
                    'error': 'Not found',
                    'message': f'User with ID {user_id} not found'
                }), 404

            return jsonify({
                'message': 'User deleted successfully'
            }), 200

        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500

    def list_users(self):
        """List all users"""
        try:
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)

            users_data = self.user_service.list_users(limit=limit, offset=offset)

            return jsonify({
                'message': 'Users retrieved successfully',
                'data': users_data,
                'count': len(users_data)
            }), 200

        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500

    def list_users_with_agents(self):
        """List users with their agents (simplified response)"""
        print("list_users_with_agents called")  # Debug print
        try:
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)

            users = self.user_service.list_users(limit=limit, offset=offset)

            # Simplified response with only name and agents
            simplified_data = []
            for user in users:
                simplified_data.append({
                    'name': user['name'] or user['phone_number'],
                    'agents': user['agents']
                })

            return jsonify({
                'message': 'Users with agents retrieved successfully',
                'data': simplified_data,
                'count': len(simplified_data)
            }), 200

        except Exception as e:
            print(f"Error in list_users_with_agents: {e}")  # Debug print
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500

    def change_subscription_plan(self, user_id):
        """Change a user's subscription plan (upgrade or downgrade)"""
        try:
            data = request.get_json()

            if not data:
                return jsonify({
                    'error': 'Request body is required',
                    'message': 'Please provide a valid JSON request body'
                }), 400

            if 'subscription_plan' not in data:
                return jsonify({
                    'error': 'Missing required field',
                    'message': 'subscription_plan is required'
                }), 400

            new_plan = data['subscription_plan']
            result = self.user_service.change_subscription_plan(int(user_id), new_plan)

            return jsonify({
                'message': 'Subscription plan updated successfully',
                'data': result['user'],
                'previous_plan': result['previous_plan'],
                'new_plan': result['new_plan'],
                'change_type': result['change_type']
            }), 200

        except ValueError as e:
            error_message = str(e)
            if 'not found' in error_message.lower():
                return jsonify({
                    'error': 'Not found',
                    'message': error_message
                }), 404
            return jsonify({
                'error': 'Validation error',
                'message': error_message
            }), 400
        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500