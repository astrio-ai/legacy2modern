#!/usr/bin/env python3
"""
Test AutoGen integration with ArchitectAgent.

This test verifies that the ArchitectAgent can be properly wrapped
with AutoGen and integrated into the group chat system.
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine.agents import (
    AI, BaseAgent, BaseExecutionEnv, ChatToFiles, DiffProcessor,
    FilesDict, GitManager, LintingManager, PrepromptsHolder, ProjectConfig,
    PromptBuilder, TokenUsageTracker, VersionManager, ParserAgent,
    ArchitectAgent, ModernizerAgent, RefactorAgent, QAAgent, CoordinatorAgent
)
from engine.agents.core_agents.base_memory import FileMemory
from engine.agents.core_agents.base_agent import AgentRole
from engine.agents.autogen_integration.autogen_wrapper import AutoGenAgentWrapper, AutoGenConfig
from engine.agents.autogen_integration.group_chat_coordinator import GroupChatCoordinator, ChatType


class TestAutoGenArchitect:
    """Test AutoGen integration with ArchitectAgent."""
    
    def __init__(self):
        """Initialize test fixtures."""
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        self.memory = FileMemory(self.test_dir)
        
        # Create basic configuration
        self.config = ProjectConfig()
        self.config.set_project_name("test-project")
        self.config.set_target_stack("react")
        
        # Create AI instance (will use environment variables)
        try:
            # Try to get API key from environment
            import os
            api_key = os.environ.get('OPENAI_API_KEY') or os.environ.get('ANTHROPIC_API_KEY')
            if api_key:
                self.ai = AI(api_key=api_key)
            else:
                # Create a mock AI for testing
                self.ai = self._create_mock_ai()
        except Exception:
            # Create a mock AI for testing
            self.ai = self._create_mock_ai()
    
    def _create_mock_ai(self):
        """Create a mock AI instance for testing."""
        class MockAI:
            def __init__(self):
                self.provider = "anthropic"
                self.model = "claude-3-sonnet-20240229"
                self.api_key = "mock-key"
                self.temperature = 0.7
                self.max_tokens = 4000
            
            async def chat(self, messages, system_prompt=None):
                return "Mock AI response for testing"
        
        return MockAI()
        
    def test_architect_agent_creation(self):
        """Test that ArchitectAgent can be created."""
        print("Testing ArchitectAgent creation...")
        
        try:
            architect = ArchitectAgent(
                ai=self.ai,
                memory=self.memory,
                config=self.config
            )
            
            assert architect.name == "ArchitectAgent"
            assert architect.role == AgentRole.ARCHITECT
            assert architect.ai is not None
            assert architect.memory is not None
            assert architect.config is not None
            
            print("✅ ArchitectAgent created successfully")
            return architect
            
        except Exception as e:
            print(f"❌ Failed to create ArchitectAgent: {e}")
            raise
    
    def test_architect_agent_autogen_wrapper(self):
        """Test that ArchitectAgent can be wrapped with AutoGen."""
        print("Testing ArchitectAgent AutoGen wrapper...")
        
        try:
            # Create architect agent
            architect = ArchitectAgent(
                ai=self.ai,
                memory=self.memory,
                config=self.config
            )
            
            # Create AutoGen config
            autogen_config = AutoGenConfig(
                enable_autogen=True,
                use_group_chat=False,
                human_in_the_loop=False,
                max_consecutive_auto_reply=5,
                fallback_on_error=True
            )
            
            # Wrap with AutoGen
            wrapped_architect = AutoGenAgentWrapper(
                base_agent=architect,
                autogen_config=autogen_config
            )
            
            assert wrapped_architect.base_agent == architect
            assert wrapped_architect.autogen_config == autogen_config
            assert hasattr(wrapped_architect, 'autogen_agent')
            
            print("✅ ArchitectAgent wrapped with AutoGen successfully")
            return wrapped_architect
            
        except Exception as e:
            print(f"❌ Failed to wrap ArchitectAgent with AutoGen: {e}")
            raise
    
    def test_architect_agent_group_chat_registration(self):
        """Test that ArchitectAgent can be registered in group chat."""
        print("Testing ArchitectAgent group chat registration...")
        
        try:
            # Create group chat coordinator
            coordinator = GroupChatCoordinator(
                ai=self.ai,
                memory=self.memory,
                config=self.config
            )
            
            # Create architect agent
            architect = ArchitectAgent(
                ai=self.ai,
                memory=self.memory,
                config=self.config
            )
            
            # Register architect agent
            agent_id = asyncio.run(coordinator.register_agent(architect, role="architect"))
            
            assert agent_id == "ArchitectAgent"
            assert "ArchitectAgent" in coordinator.agents
            assert coordinator.agent_roles["ArchitectAgent"] == "architect"
            
            print("✅ ArchitectAgent registered in group chat successfully")
            return coordinator, architect
            
        except Exception as e:
            print(f"❌ Failed to register ArchitectAgent in group chat: {e}")
            raise
    
    def test_architect_agent_message_processing(self):
        """Test that ArchitectAgent can process messages."""
        print("Testing ArchitectAgent message processing...")
        
        try:
            # Create architect agent
            architect = ArchitectAgent(
                ai=self.ai,
                memory=self.memory,
                config=self.config
            )
            
            # Store parser output in memory first
            parser_output = {
                'pages': ['index.html', 'about.html'],
                'components': ['header', 'footer'],
                'assets': ['style.css', 'script.js']
            }
            asyncio.run(self.memory.set('parser_output', parser_output))
            
            # Test message processing
            test_message = {
                'type': 'create_architecture',
                'parser_output': parser_output
            }
            
            result = asyncio.run(architect.process_message(test_message))
            
            print(f"Message processing result: {result}")
            
            assert result is not None
            assert 'success' in result or 'type' in result
            
            print("✅ ArchitectAgent message processing successful")
            return architect
            
        except Exception as e:
            print(f"❌ Failed to process messages with ArchitectAgent: {e}")
            raise
    
    def test_architect_agent_task_execution(self):
        """Test that ArchitectAgent can execute tasks."""
        print("Testing ArchitectAgent task execution...")
        
        try:
            # Create architect agent
            architect = ArchitectAgent(
                ai=self.ai,
                memory=self.memory,
                config=self.config
            )
            
            # Test task execution
            test_task = {
                'type': 'full_architecture_design',
                'parser_output': {
                    'pages': ['index.html', 'about.html'],
                    'components': ['header', 'footer'],
                    'assets': ['style.css', 'script.js']
                }
            }
            
            result = asyncio.run(architect.execute_task(test_task))
            
            assert result is not None
            assert 'success' in result
            
            print("✅ ArchitectAgent task execution successful")
            return architect
            
        except Exception as e:
            print(f"❌ Failed to execute tasks with ArchitectAgent: {e}")
            raise
    
    def test_full_autogen_integration(self):
        """Test full AutoGen integration with ArchitectAgent."""
        print("Testing full AutoGen integration...")
        
        try:
            # Create group chat coordinator
            coordinator = GroupChatCoordinator(
                ai=self.ai,
                memory=self.memory,
                config=self.config
            )
            
            # Create and register multiple agents
            agents = {}
            
            # Parser Agent
            parser = ParserAgent(ai=self.ai, memory=self.memory, config=self.config)
            agent_id = asyncio.run(coordinator.register_agent(parser, role="parser"))
            agents['parser'] = parser
            
            # Architect Agent
            architect = ArchitectAgent(ai=self.ai, memory=self.memory, config=self.config)
            agent_id = asyncio.run(coordinator.register_agent(architect, role="architect"))
            agents['architect'] = architect
            
            # Modernizer Agent
            modernizer = ModernizerAgent(ai=self.ai, memory=self.memory, config=self.config)
            agent_id = asyncio.run(coordinator.register_agent(modernizer, role="modernizer"))
            agents['modernizer'] = modernizer
            
            # Verify all agents are registered
            assert len(coordinator.agents) == 3
            assert "ParserAgent" in coordinator.agents
            assert "ArchitectAgent" in coordinator.agents
            assert "ModernizerAgent" in coordinator.agents
            
            # Test group chat creation
            session_id = asyncio.run(coordinator.create_group_chat(
                chat_type=ChatType.PLANNING,
                topic="Test website modernization",
                participants=["ParserAgent", "ArchitectAgent", "ModernizerAgent"],
                max_rounds=3
            ))
            
            assert session_id is not None
            assert session_id in coordinator.active_sessions
            
            print("✅ Full AutoGen integration successful")
            return coordinator, agents
            
        except Exception as e:
            print(f"❌ Full AutoGen integration failed: {e}")
            raise


def main():
    """Run all tests."""
    print("🧪 Testing AutoGen Integration with ArchitectAgent")
    print("=" * 60)
    
    test_instance = TestAutoGenArchitect()
    
    try:
        # Test 1: Basic agent creation
        test_instance.test_architect_agent_creation()
        
        # Test 2: AutoGen wrapper
        test_instance.test_architect_agent_autogen_wrapper()
        
        # Test 3: Group chat registration
        test_instance.test_architect_agent_group_chat_registration()
        
        # Test 4: Message processing
        test_instance.test_architect_agent_message_processing()
        
        # Test 5: Task execution
        test_instance.test_architect_agent_task_execution()
        
        # Test 6: Full integration
        test_instance.test_full_autogen_integration()
        
        print("\n🎉 All tests passed! ArchitectAgent is properly integrated with AutoGen.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == '__main__':
    main() 