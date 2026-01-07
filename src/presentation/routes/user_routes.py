from flask import Blueprint
from src.infrastructure.database.connection import get_db_context
from src.infrastructure.repositories.postgres_user_repository import PostgresUserRepository
from src.application.services.user_service import UserService
from src.presentation.controllers.user_controller import UserController


def create_user_blueprint() -> Blueprint:
    """Create and configure user blueprint"""
    bp = Blueprint('users', __name__, url_prefix='/api/users')

    # Helper function to create controller with proper session management
    def with_user_controller(handler_method):
        """Decorator to provide controller with proper DB session management"""
        def wrapper(*args, **kwargs):
            with get_db_context() as db:
                user_repo = PostgresUserRepository(db)
                user_service = UserService(user_repo)
                controller = UserController(user_service)
                return getattr(controller, handler_method)(*args, **kwargs)
        wrapper.__name__ = handler_method
        return wrapper

    # Register routes with session management
    bp.route('', methods=['POST'])(with_user_controller('create_user'))
    bp.route('/<int:user_id>', methods=['GET'])(with_user_controller('get_user'))
    bp.route('/<int:user_id>', methods=['PUT'])(with_user_controller('update_user'))
    bp.route('/<int:user_id>', methods=['DELETE'])(with_user_controller('delete_user'))
    bp.route('/phone/<phone_number>', methods=['GET'])(with_user_controller('get_user_by_phone'))
    bp.route('', methods=['GET'])(with_user_controller('list_users'))
    bp.route('/with-agents', methods=['GET'])(with_user_controller('list_users_with_agents'))

    return bp