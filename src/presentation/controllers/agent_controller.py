from flask import request, jsonify
from src.application.services.agent_service import AgentService
from src.infrastructure.ai.vertex_ai_service import VertexAIService


class AgentController:
    """Controller for agent endpoints"""

    def __init__(self, agent_service: AgentService):
        self.agent_service = agent_service

    def _normalize_input(self, data: dict) -> dict:
        """Normalize camelCase input to snake_case"""
        field_mapping = {
            'isActive': 'is_active',
            'autoRespond': 'auto_respond',
            'learningMode': 'learning_mode',
            'responseTemperature': 'response_temperature',
            'maxResponseTokens': 'max_response_tokens',
            'systemPrompt': 'system_prompt'
        }
        normalized = {}
        for key, value in data.items():
            normalized_key = field_mapping.get(key, key)
            normalized[normalized_key] = value
        return normalized

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

            # Normalize input data
            normalized_data = self._normalize_input(data)

            # Create the agent
            agent = self.agent_service.create_agent(normalized_data)

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

            # Normalize input data (camelCase to snake_case)
            normalized_data = self._normalize_input(data)

            # Update the agent
            success = self.agent_service.update_agent(int(agent_id), normalized_data)

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

    def get_agent_users(self, agent_id):
        """Get all users assigned to an agent"""
        try:
            users = self.agent_service.get_agent_users(int(agent_id))

            return jsonify({
                'message': 'Agent users retrieved successfully',
                'data': users,
                'count': len(users)
            }), 200

        except ValueError as e:
            return jsonify({
                'error': 'Not found',
                'message': str(e)
            }), 404
        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': 'An unexpected error occurred while processing your request'
            }), 500

    def add_users_to_agent(self, agent_id):
        """Add users to an agent with optional language/validity_days"""
        try:
            data = request.get_json()

            if not data:
                return jsonify({
                    'error': 'Request body is required',
                    'message': 'Please provide a valid JSON request body'
                }), 400

            # Support both 'users' array format and legacy 'user_ids' format
            users = data.get('users') or []
            user_ids = data.get('user_ids') or data.get('userIds', [])
            
            # Build users_data list
            users_data = []
            
            if users and isinstance(users, list):
                # New format: array of user objects with user_id, language, validity_days
                for user in users:
                    user_id = user.get('user_id') or user.get('userId')
                    if user_id:
                        users_data.append({
                            'user_id': user_id,
                            'language': user.get('language'),
                            'validity_days': user.get('validity_days') or user.get('validityDays')
                        })
            elif user_ids and isinstance(user_ids, list):
                # Legacy format: just array of user IDs
                users_data = [{'user_id': uid} for uid in user_ids]
            
            if not users_data:
                return jsonify({
                    'error': 'Invalid request',
                    'message': 'users array or user_ids must be provided'
                }), 400

            result = self.agent_service.add_users_to_agent(int(agent_id), users_data)

            return jsonify({
                'message': 'Users added to agent',
                'data': result
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

    def update_agent_users(self, agent_id):
        """Update language/validity for users assigned to an agent"""
        try:
            data = request.get_json()

            if not data:
                return jsonify({
                    'error': 'Request body is required',
                    'message': 'Please provide a valid JSON request body'
                }), 400

            users = data.get('users') or []
            if not users or not isinstance(users, list):
                return jsonify({
                    'error': 'Invalid request',
                    'message': 'users array must be provided'
                }), 400

            # Build users_data list
            users_data = []
            for user in users:
                user_id = user.get('user_id') or user.get('userId')
                if user_id:
                    users_data.append({
                        'user_id': user_id,
                        'language': user.get('language'),
                        'validity_days': user.get('validity_days') or user.get('validityDays')
                    })

            if not users_data:
                return jsonify({
                    'error': 'Invalid request',
                    'message': 'users array must contain valid user objects with user_id'
                }), 400

            result = self.agent_service.update_agent_users(int(agent_id), users_data)

            return jsonify({
                'message': 'Agent users updated',
                'data': result
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

    def remove_users_from_agent(self, agent_id):
        """Remove users from an agent"""
        try:
            data = request.get_json()

            if not data:
                return jsonify({
                    'error': 'Request body is required',
                    'message': 'Please provide a valid JSON request body'
                }), 400

            user_ids = data.get('user_ids') or data.get('userIds', [])
            if not user_ids or not isinstance(user_ids, list):
                return jsonify({
                    'error': 'Invalid request',
                    'message': 'user_ids must be a non-empty array'
                }), 400

            result = self.agent_service.remove_users_from_agent(int(agent_id), user_ids)

            return jsonify({
                'message': 'Users removed from agent',
                'data': result
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

    def test_model(self, agent_id: int):
        """Test the AI model and corpus with a sample question using agent configuration
        
        POST /api/agents/<agent_id>/test-model
        Body: {
            "question": "Your test question",
            "language": "es" (optional, default: es)
        }
        
        Uses RAG_CORPUS_NAME from environment and RAG is always enabled.
        """
        try:
            # Get agent configuration
            agent = self.agent_service.get_agent_by_id(agent_id)
            if not agent:
                return jsonify({
                    'error': 'Agent not found',
                    'message': f'Agent with ID {agent_id} does not exist'
                }), 404

            data = request.get_json()

            if not data:
                return jsonify({
                    'error': 'Request body is required',
                    'message': 'Please provide a valid JSON request body with a question'
                }), 400

            question = data.get('question')
            if not question:
                return jsonify({
                    'error': 'Missing required field',
                    'message': 'question field is required'
                }), 400

            # Use agent configuration with optional overrides from request
            language = data.get('language', 'es')
            
            # Get agent's AI parameters
            system_prompt = agent.get('system_prompt')
            temperature = float(agent.get('response_temperature', 0.7))
            max_tokens = agent.get('max_response_tokens', 500)

            # Initialize AI service (uses RAG_CORPUS_NAME from env by default)
            ai_service = VertexAIService()

            # Get corpus info
            corpus_info = ai_service.get_corpus_info()

            # Retrieve relevant contexts from RAG corpus
            retrieved_contexts = []
            if ai_service.rag_corpus:
                retrieved_contexts = ai_service.retrieve_relevant_contexts(question, top_k=5)

            # Generate response using agent configuration
            response_text = ai_service.generate_response(
                question=question,
                context="Test from dashboard",
                language=language,
                use_rag=True,
                max_output_tokens=max_tokens,
                custom_system_prompt=system_prompt,
                temperature=temperature
            )

            return jsonify({
                'message': 'Model test completed successfully',
                'source': 'testing',
                'data': {
                    'question': question,
                    'response': response_text,
                    'language': language,
                    'corpus_info': corpus_info,
                    'retrieved_contexts': retrieved_contexts,
                    'contexts_count': len(retrieved_contexts),
                    'agent': {
                        'id': agent.get('id'),
                        'name': agent.get('name'),
                        'type': agent.get('type'),
                        'system_prompt_used': bool(system_prompt),
                        'temperature': temperature,
                        'max_tokens': max_tokens
                    }
                }
            }), 200

        except ValueError as e:
            return jsonify({
                'error': 'Configuration error',
                'message': str(e)
            }), 400
        except Exception as e:
            return jsonify({
                'error': 'Internal server error',
                'message': f'An error occurred while testing the model: {str(e)}'
            }), 500
