import streamlit as st
from crewai import Agent, Task, Crew, Process

# Define a dictionary of available crewAI examples
crewai_examples = {
  "Marketing Campaign": {
      "description": "Generate a marketing plan, target audience research, and ad copy.",
      "agents": [
          "Market Researcher",
          "Target Audience Analyst",
          "Content Writer",
          "Campaign Manager",
      ],
      "tasks": [
          "Generate Marketing Plan",
          "Research Target Audience",
          "Write Ad Copy",
          "Create Campaign Schedule",
      ],
  },
  # Add more examples as needed
}

# Create the Streamlit app
st.title("Run crewAI Examples")

# API Key inputs
openai_api_key = st.text_input("Enter your OpenAI API Key", type="password")
serper_api_key = st.text_input("Enter your Serper API Key", type="password")

# Select an example
selected_example = st.selectbox("Select a crewAI example", list(crewai_examples.keys()))

# Display example description
st.write(f"**Description:** {crewai_examples[selected_example]['description']}")

# User inputs
inputs = {}
for task in crewai_examples[selected_example]["tasks"]:
  input_label = f"Input for {task}:"
  inputs[task] = st.text_area(input_label, value="Enter your input here...")

# Run the selected example
if st.button("Run Example"):
  if not openai_api_key or not serper_api_key:
      st.error("Please enter both API keys to proceed.")
  else:
      # Create agents dynamically based on selected example
      agents = []
      for agent_role in crewai_examples[selected_example]["agents"]:
          agents.append(Agent(role=agent_role, goal=f"Perform {agent_role} tasks."))

      # Create tasks dynamically based on selected example and user inputs
      tasks = []
      for task_name, user_input in inputs.items():
          tasks.append(
              Task(
                  description=f"{task_name}: {user_input}",
                  agent=agents[crewai_examples[selected_example]["agents"].index(agent_role)],
              )
          )

      # Instantiate the crew with a sequential process
      crew = Crew(
          agents=agents, 
          tasks=tasks, 
          process=Process.sequential,
          verbose=True,
          config={
              "openai_api_key": openai_api_key,
              "serper_api_key": serper_api_key
          }
      )

      # Kick off the crew
      try:
          with st.spinner("Processing..."):
              result = crew.kickoff()

          # Display the results
          st.write("**Results:**")
          st.write(result)

      except Exception as e:
          st.error(f"An error occurred: {str(e)}")
