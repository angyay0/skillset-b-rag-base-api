from flask import Blueprint
from src.infrastructure.database.connection import get_db_context
from src.infrastructure.repositories.postgres_agent_repository import PostgresAgentRepository
from src.application.services.agent_service import AgentService
from src.presentation.controllers.agent_controller import AgentController


def create_agent_blueprint() -> Blueprint:
    """Create and configure agent blueprint"""
    bp = Blueprint('agents', __name__, url_prefix='/api/agents')

    # Helper function to create controller with proper session management
    def with_agent_controller(handler_method):
        """Decorator to provide controller with proper DB session management"""
        def wrapper(*args, **kwargs):
            with get_db_context() as db:
                agent_repo = PostgresAgentRepository(db)
                agent_service = AgentService(agent_repo)
                controller = AgentController(agent_service)
                return getattr(controller, handler_method)(*args, **kwargs)
        wrapper.__name__ = handler_method
        return wrapper

    # Register routes with session management
    bp.route('', methods=['POST'])(with_agent_controller('create_agent'))
    bp.route('/<int:agent_id>', methods=['GET'])(with_agent_controller('get_agent'))
    bp.route('/<int:agent_id>', methods=['PUT'])(with_agent_controller('update_agent'))
    bp.route('/<int:agent_id>', methods=['DELETE'])(with_agent_controller('delete_agent'))
    bp.route('/name/<name>', methods=['GET'])(with_agent_controller('get_agent_by_name'))
    bp.route('/type/<agent_type>', methods=['GET'])(with_agent_controller('get_agents_by_type'))
    bp.route('', methods=['GET'])(with_agent_controller('get_all_agents'))
    bp.route('/active', methods=['GET'])(with_agent_controller('get_active_agents'))

    return bp