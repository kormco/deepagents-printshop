#!/bin/bash
# Run the DeepAgent Scribe research agent

echo "Starting DeepAgent Scribe Research Agent..."
echo ""

# Navigate to the agents directory
cd /app/agents/research_agent

# Run the agent
python agent.py "$@"
