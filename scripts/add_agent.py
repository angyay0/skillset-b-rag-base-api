#!/usr/bin/env python3
"""
Script to add agents to the database
"""
import sys
import os
import argparse
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from src.infrastructure.database.connection import get_db_context
from src.infrastructure.repositories.postgres_agent_repository import PostgresAgentRepository
from src.domain.entities.agent import Agent

# Load environment variables
load_dotenv()


def add_agent(name: str, agent_type: str, description: str = None, configuration: dict = None):
    """Add a new agent to the database"""

    with get_db_context() as db:
        agent_repo = PostgresAgentRepository(db)

        # Check if agent already exists
        existing_agent = agent_repo.get_by_name(name)
        if existing_agent:
            print(f"❌ Agent with name '{name}' already exists!")
            print(f"   ID: {existing_agent.id}")
            print(f"   Name: {existing_agent.name}")
            print(f"   Type: {existing_agent.type}")
            print(f"   Description: {existing_agent.description or 'N/A'}")
            print(f"   Active: {existing_agent.is_active}")
            print(f"   Created: {existing_agent.created_at}")
            return False

        # Create new agent
        agent = Agent(
            id=None,
            name=name,
            type=agent_type,
            description=description,
            configuration=configuration,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        created_agent = agent_repo.create(agent)

        print(f"✅ Agent created successfully!")
        print(f"   ID: {created_agent.id}")
        print(f"   Name: {created_agent.name}")
        print(f"   Type: {created_agent.type}")
        print(f"   Description: {created_agent.description or 'N/A'}")
        print(f"   Configuration: {json.dumps(created_agent.configuration) if created_agent.configuration else 'N/A'}")
        print(f"   Active: {created_agent.is_active}")
        print(f"   Created: {created_agent.created_at}")

        return True


def list_agents():
    """List all agents in the database"""
    
    with get_db_context() as db:
        agent_repo = PostgresAgentRepository(db)
        agents = agent_repo.get_all(limit=1000)
        
        if not agents:
            print("No agents found in the database.")
            return
        
        print(f"\n📋 Total agents: {len(agents)}\n")
        print(f"{'ID':<5} {'Name':<25} {'Type':<20} {'Description':<30} {'Status':<10}")
        print("-" * 95)
        
        for agent in agents:
            status = "✓ Active" if agent.is_active else "✗ Inactive"
            desc = (agent.description[:27] + '...') if agent.description and len(agent.description) > 30 else (agent.description or 'N/A')
            print(f"{agent.id:<5} {agent.name:<25} {agent.type:<20} {desc:<30} {status:<10}")


def get_agent(agent_id: int = None, name: str = None):
    """Get agent details by ID or name"""
    
    with get_db_context() as db:
        agent_repo = PostgresAgentRepository(db)
        
        if agent_id:
            agent = agent_repo.get_by_id(agent_id)
        elif name:
            agent = agent_repo.get_by_name(name)
        else:
            print("❌ Please provide either --id or --name")
            return False
        
        if not agent:
            print(f"❌ Agent not found!")
            return False
        
        print(f"\n📋 Agent Details:\n")
        print(f"   ID: {agent.id}")
        print(f"   Name: {agent.name}")
        print(f"   Type: {agent.type}")
        print(f"   Description: {agent.description or 'N/A'}")
        print(f"   Configuration: {json.dumps(agent.configuration, indent=2) if agent.configuration else 'N/A'}")
        print(f"   Active: {agent.is_active}")
        print(f"   Created: {agent.created_at}")
        print(f"   Updated: {agent.updated_at}")
        
        return True


def update_agent(agent_id: int, name: str = None, agent_type: str = None, description: str = None, configuration: str = None):
    """Update an existing agent"""
    
    with get_db_context() as db:
        agent_repo = PostgresAgentRepository(db)
        
        agent = agent_repo.get_by_id(agent_id)
        if not agent:
            print(f"❌ Agent with ID {agent_id} not found!")
            return False
        
        # Update fields if provided
        if name:
            agent.name = name
        if agent_type:
            agent.type = agent_type
        if description:
            agent.description = description
        if configuration:
            try:
                agent.configuration = json.loads(configuration)
            except json.JSONDecodeError:
                print("❌ Invalid JSON for configuration")
                return False
        
        agent.updated_at = datetime.utcnow()
        success = agent_repo.update(agent)
        
        if success:
            print(f"✅ Agent updated successfully!")
            print(f"   ID: {agent.id}")
            print(f"   Name: {agent.name}")
            print(f"   Type: {agent.type}")
            print(f"   Description: {agent.description or 'N/A'}")
        else:
            print("❌ Failed to update agent")
        
        return success


def deactivate_agent(agent_id: int):
    """Deactivate an agent"""
    
    with get_db_context() as db:
        agent_repo = PostgresAgentRepository(db)
        
        agent = agent_repo.get_by_id(agent_id)
        if not agent:
            print(f"❌ Agent with ID {agent_id} not found!")
            return False
        
        agent.is_active = False
        agent.updated_at = datetime.utcnow()
        success = agent_repo.update(agent)
        
        if success:
            print(f"✅ Agent deactivated successfully!")
            print(f"   ID: {agent.id}")
            print(f"   Name: {agent.name}")
            print(f"   Status: Inactive")
        else:
            print("❌ Failed to deactivate agent")
        
        return success


def activate_agent(agent_id: int):
    """Activate an agent"""
    
    with get_db_context() as db:
        agent_repo = PostgresAgentRepository(db)
        
        agent = agent_repo.get_by_id(agent_id)
        if not agent:
            print(f"❌ Agent with ID {agent_id} not found!")
            return False
        
        agent.is_active = True
        agent.updated_at = datetime.utcnow()
        success = agent_repo.update(agent)
        
        if success:
            print(f"✅ Agent activated successfully!")
            print(f"   ID: {agent.id}")
            print(f"   Name: {agent.name}")
            print(f"   Status: Active")
        else:
            print("❌ Failed to activate agent")
        
        return success


def delete_agent(agent_id: int, force: bool = False):
    """Delete an agent"""
    
    with get_db_context() as db:
        agent_repo = PostgresAgentRepository(db)
        
        agent = agent_repo.get_by_id(agent_id)
        if not agent:
            print(f"❌ Agent with ID {agent_id} not found!")
            return False
        
        if not force:
            confirm = input(f"Are you sure you want to delete agent '{agent.name}' (ID: {agent.id})? [y/N]: ")
            if confirm.lower() != 'y':
                print("Cancelled.")
                return False
        
        success = agent_repo.delete(agent_id)
        
        if success:
            print(f"✅ Agent deleted successfully!")
            print(f"   Deleted: {agent.name} (ID: {agent.id})")
        else:
            print("❌ Failed to delete agent")
        
        return success


def main():
    parser = argparse.ArgumentParser(description='Manage agents in the database')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add agent command
    add_parser = subparsers.add_parser('add', help='Add a new agent')
    add_parser.add_argument('name', help='Agent name')
    add_parser.add_argument('type', help='Agent type (e.g., customer_support, sales, general)')
    add_parser.add_argument('--description', help='Agent description', default=None)
    add_parser.add_argument('--config', help='Agent configuration as JSON string', default=None)
    
    # List agents command
    list_parser = subparsers.add_parser('list', help='List all agents')
    
    # Get agent command
    get_parser = subparsers.add_parser('get', help='Get agent details')
    get_parser.add_argument('--id', type=int, help='Agent ID')
    get_parser.add_argument('--name', help='Agent name')
    
    # Update agent command
    update_parser = subparsers.add_parser('update', help='Update an agent')
    update_parser.add_argument('id', type=int, help='Agent ID')
    update_parser.add_argument('--name', help='New agent name')
    update_parser.add_argument('--type', help='New agent type')
    update_parser.add_argument('--description', help='New description')
    update_parser.add_argument('--config', help='New configuration as JSON string')
    
    # Deactivate agent command
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate an agent')
    deactivate_parser.add_argument('id', type=int, help='Agent ID')
    
    # Activate agent command
    activate_parser = subparsers.add_parser('activate', help='Activate an agent')
    activate_parser.add_argument('id', type=int, help='Agent ID')
    
    # Delete agent command
    delete_parser = subparsers.add_parser('delete', help='Delete an agent')
    delete_parser.add_argument('id', type=int, help='Agent ID')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    
    args = parser.parse_args()
    
    if args.command == 'add':
        config = json.loads(args.config) if args.config else None
        add_agent(args.name, args.type, args.description, config)
    elif args.command == 'list':
        list_agents()
    elif args.command == 'get':
        get_agent(args.id, args.name)
    elif args.command == 'update':
        update_agent(args.id, args.name, args.type, args.description, args.config)
    elif args.command == 'deactivate':
        deactivate_agent(args.id)
    elif args.command == 'activate':
        activate_agent(args.id)
    elif args.command == 'delete':
        delete_agent(args.id, args.force)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
