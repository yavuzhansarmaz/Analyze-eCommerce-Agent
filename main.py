#!/usr/bin/env python3
"""
Simple CLI for the Data Analysis Agent.
"""

import sys
import os
import logging
import time

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from agent import create_analysis_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleCLI:
    """Simple command-line interface for the Data Analysis Agent."""

    def __init__(self, agent=None):
        """Initialize the CLI interface.

        Args:
            agent: Pre-initialized analysis agent. If None, will be created automatically.
        """
        self.agent = agent
        self.session_start_time = time.time()

        if self.agent is None:
            self.agent = self._create_analysis_agent()

    def _create_analysis_agent(self):
        """Create and initialize the analysis agent with proper error handling."""
        try:
            logger.info("Initializing Data Analysis Agent...")
            agent = create_analysis_agent()
            logger.info("Agent ready")
            return agent
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            print(f"❌ Agent Initialization Error: {e}")
            print("\nTroubleshooting steps:")
            print("1. Check your internet connection")
            print("2. Verify BigQuery credentials are properly configured")
            print("3. Ensure the service account file exists and has correct permissions")
            print("4. Check that the BigQuery dataset is accessible")
            print("5. Review the agent.log file for detailed error information")
            sys.exit(1)

    def run(self):
        """Run the interactive CLI."""
        print("🤖 Data Analysis Agent")
        print("=" * 30)
        print("Ask me questions about e-commerce data!")
        print("Examples:")
        print("  'analyze customer segments'")
        print("  'show product performance'")
        print("  'sales trends analysis'")
        print("  'quit' to exit")
        print()

        while True:
            try:
                user_input = input("💬 > ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'bye']:
                    session_time = time.time() - self.session_start_time
                    print("👋 Goodbye!")
                    print(f"⏱️  Session duration: {session_time:.1f} seconds")
                    break

                if user_input.lower() in ['help', '?']:
                    self._show_help()
                    continue

                # Process the request
                print(f"🔍 Analyzing: '{user_input}'")
                print("⏳ Processing...")
                start_time = time.time()

                result_state = self.agent.analyze(user_input)

                # Display results
                insights_text = self.agent.get_insights_text(result_state)

                print("\n📊 RESULTS:")
                print("-" * 30)
                print(insights_text)

                # Show any errors
                errors = result_state.get("errors", [])
                if errors:
                    print("\n⚠️  Errors:")
                    for error in errors:
                        print(f"  • {error}")

                # Show processing time
                end_time = time.time()
                processing_time = end_time - start_time
                print(f"\n⏱️  Processing completed in {processing_time:.2f} seconds")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                print("💡 Tip: Type 'quit', 'exit', or 'bye' to exit anytime.")
                break
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                print(f"❌ Error: {e}")
                print("Please try again.")
                print("💡 Tip: Type 'quit' to exit.")

    def _show_help(self):
        """Show help information."""
        print("\n📖 HELP:")
        print("-" * 20)
        print("Ask questions like:")
        print("• 'analyze customer segments'")
        print("• 'show product performance'")
        print("• 'sales trends analysis'")
        print("• 'geographic sales patterns'")
        print("• 'customer behavior analysis'")
        print()
        print("Features:")
        print("• ⏱️  Shows processing time for each analysis")
        print("• ⏱️  Shows total session time when exiting")
        print()
        print("Type 'quit' to exit.")
        print()

def main():
    """Main entry point."""
    # Check configuration first
    try:
        config = get_config()
        logger.debug("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        print(f"❌ Configuration Error: {e}")
        print("\nPlease ensure you have:")
        print("1. Created a .env file based on env_example.txt")
        print("2. Set your GOOGLE_API_KEY for Gemini")
        print("3. Configured BigQuery credentials (GOOGLE_APPLICATION_CREDENTIALS)")
        sys.exit(1)

    # Start the CLI
    try:
        cli = SimpleCLI()
        cli.run()
    except Exception as e:
        logger.error(f"CLI error: {e}")
        print(f"❌ Error: {e}")
        print("Check the agent.log file for more details.")
        sys.exit(1)

if __name__ == "__main__":
    main()