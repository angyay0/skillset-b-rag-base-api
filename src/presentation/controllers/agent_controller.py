from flask import request, jsonify
from src.application.services.agent_service import AgentService


class AgentController:
    """Controller for agent endpoints"""

    def __init__(self, agent_service: AgentService):
        self.agent_service = agent_service

    def create_agent(self):
        """Create a new agent"""
        try:
            data = request.get_json()

            if not data:
                return jsonify({
                    'error': 'Request body is required',
                    'message': 'Please provide a valid JSON request body'
                }), 400

            # Validate required fields
            required_fields = ['name', 'type']
            missing_fields = [field for field in required_fields if field not in data]

            if missing_fields:
                return jsonify({
                    'error': 'Missing required fields',
                    'missing_fields': missing_fields
                }), 400

            # Create the agent
            agent = self.agent_service.create_agent(data)

            # Respond with 201 and the created agent data
            response_data = self.agent_service._to_response_dict(agent)

            return jsonify({
                'message': 'Agent created successfully',
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

    def get_agent(self, agent_id):
        """Get an agent by ID"""
        try:
            agent_data = self.agent_service.get_agent_by_id(int(agent_id))

            if not agent_data:
                return jsonify({
                    'error': 'Not found',
                    'message': f'Agent with ID {agent_id} not found'
                }), 404

            return jsonify({
                'message': 'Agent retrieved successfully',
                'data': agent_data
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

    def get_agent_by_name(self, name):
        """Get an agent by name"""
        try:
            agent_data = self.agent_service.get_agent_by_name(name)

            if not agent_data:
                return jsonify({
                    'error': 'Not found',
                    'message': f'Agent with name {name} not found'
                }), 404

            return jsonify({
                'message': 'Agent retrieved successfully',
                'data': agent_data
            }), 200

        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500

    def get_agents_by_type(self, agent_type):
        """Get agents by type"""
        try:
            agents_data = self.agent_service.get_agents_by_type(agent_type)

            return jsonify({
                'message': 'Agents retrieved successfully',
                'data': agents_data,
                'count': len(agents_data)
            }), 200

        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500

    def get_all_agents(self):
        """Get all agents"""
        try:
            agents_data = self.agent_service.get_all_agents()

            return jsonify({
                'message': 'Agents retrieved successfully',
                'data': agents_data,
                'count': len(agents_data)
            }), 200

        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500

    def get_active_agents(self):
        """Get active agents"""
        try:
            agents_data = self.agent_service.get_active_agents()

            return jsonify({
                'message': 'Active agents retrieved successfully',
                'data': agents_data,
                'count': len(agents_data)
            }), 200

        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500

    def update_agent(self, agent_id):
        """Update an agent"""
        try:
            data = request.get_json()

            if not data:
                return jsonify({
                    'error': 'Request body is required',
                    'message': 'Please provide a valid JSON request body'
                }), 400

            # Update the agent
            success = self.agent_service.update_agent(int(agent_id), data)

            if not success:
                return jsonify({
                    'error': 'Update failed',
                    'message': 'Failed to update the agent'
                }), 500

            # Get updated agent data
            updated_agent = self.agent_service.get_agent_by_id(int(agent_id))

            return jsonify({
                'message': 'Agent updated successfully',
                'data': updated_agent
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

    def delete_agent(self, agent_id):
        """Delete an agent"""
        try:
            success = self.agent_service.delete_agent(int(agent_id))

            if not success:
                return jsonify({
                    'error': 'Delete failed',
                    'message': 'Failed to delete the agent'
                }), 500

            return jsonify({
                'message': 'Agent deleted successfully'
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