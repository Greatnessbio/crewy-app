import streamlit as st
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool, FileReadTool, FileWriteTool

# Define a dictionary of available crewAI examples
crewai_examples = {
  "Prepare for meetings": {
      "description": "Prepare for your next meeting by summarizing documents and generating key talking points.",
      "agents": ["Researcher", "Analyst", "Writer"],
      "tasks": ["Summarize Document", "Analyze Trends", "Generate Talking Points"],
  },
  "Trip Planner Crew": {
      "description": "Plan your next trip with the help of AI agents who can find flights, hotels, and activities.",
      "agents": ["Travel Agent", "Researcher", "Budget Analyst"],
      "tasks": ["Find Flights", "Find Hotels", "Find Activities", "Calculate Budget"],
  },
  "Create Instagram Post": {
      "description": "Generate an engaging Instagram post with relevant hashtags and captions.",
      "agents": ["Content Creator", "Image Editor", "Hashtag Generator"],
      "tasks": ["Write Caption", "Edit Image", "Generate Hashtags"],
  },
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
}

# Create the Streamlit app
st.title("Run crewAI Examples")

# API Key inputs
serper_api_key = st.text_input("Enter your Serper API Key", type="password")
openai_api_key = st.text_input("Enter your OpenAI API Key", type="password")

# Select an example
selected_example = st.selectbox("Select a crewAI example", list(crewai_examples.keys()))

# Display example description
st.write(f"**Description:** {crewai_examples[selected_example]['description']}")

# User inputs
inputs = {}
for task in crewai_examples[selected_example]["tasks"]:
  input_label = f"Input for {task}:"
  inputs[task] = st.text_area(input_label)

# Run the selected example
if st.button("Run Example"):
  if not serper_api_key or not openai_api_key:
      st.error("Please enter both Serper and OpenAI API keys.")
  else:
      # Instantiate tools with API keys
      search_tool = SerperDevTool(api_key=serper_api_key)
      file_read_tool = FileReadTool()
      file_write_tool = FileWriteTool()

      # Create agents dynamically based on selected example
      agents = []
      for agent_role in crewai_examples[selected_example]["agents"]:
          if agent_role == "Market Researcher":
              agents.append(
                  Agent(
                      role=agent_role,
                      goal=f"Perform {agent_role} tasks.",
                      tools=[search_tool],
                  )
              )
          elif agent_role == "Content Writer":
              agents.append(
                  Agent(
                      role=agent_role,
                      goal=f"Perform {agent_role} tasks.",
                      tools=[file_read_tool],
                  )
              )
          elif agent_role == "Campaign Manager":
              agents.append(
                  Agent(
                      role=agent_role,
                      goal=f"Perform {agent_role} tasks.",
                      tools=[file_write_tool],
                  )
              )
          else:
              agents.append(Agent(role=agent_role, goal=f"Perform {agent_role} tasks."))

      # Create tasks dynamically based on selected example and user inputs
      tasks = []
      for task_name, user_input in inputs.items():
          tasks.append(
              Task(
                  description=f"{task_name}: {user_input}",
                  agent=agents[
                      crewai_examples[selected_example]["agents"].index(agent_role)
                  ],
              )
          )

      # Instantiate the crew with a sequential process
      crew = Crew(
          agents=agents, 
          tasks=tasks, 
          process=Process.sequential,
          verbose=True,
          config={"openai_api_key": openai_api_key}
      )

      # Kick off the crew
      try:
          with st.spinner("Running CrewAI..."):
              result = crew.kickoff()

          # Display the results
          st.write("**Results:**")
          st.write(result)

      except Exception as e:
          st.error(f"An error occurred: {str(e)}")
