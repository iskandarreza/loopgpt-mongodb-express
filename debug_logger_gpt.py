from loopgpt.tools.agent_manager import MessageAgent, ListAgents
from loopgpt.tools.base_tool import BaseTool
from uuid import uuid4

import loopgpt
import json
import requests

def post_data(data: dict, url_params: str, url: str):
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost'
    }

    json_data = json.dumps({"data": data}, sort_keys=True, indent=4)
    requests.post(f"{url}{url_params}", headers=headers, json=json.loads(json_data))

class ToolConfig:
    def __init__(self, wrapper) -> None:
        self.wrapper = wrapper

    # Tool set grouped by utility
    agent_tools = [
        "list_agents",
        "message_agent",
        "create_agent",
        "delete_agent",
    ]

    file_read_tools = [
        "list_files",
        "check_if_file_exists",
        "read_from_file",
        "get_cwd"
    ]

    file_write_tools = [
        "append_to_file",
        "write_to_file",
        "make_directory",
    ]    

    code_tools = [
        "review_code",
        "improve_code",
        "write_tests"
    ]

    web_tools = [
        "google_search",
        "browser",
    ]

    dangerous_tools = [
        "execute_python_file",
        "shell"
    ]

    # misc uncategorized tools
    evaluate_math = "evaluate_math"
    ask_user = "ask_user"


    def add_tools(self, tool_set={}, tools_list=[]):
        tools = {}
        for tool in tools_list:
            _tool = tool_set.get(tool)
            tools[tool] = _tool
            if self.wrapper != None:
                tools["list_agents"] = _ListAgents(self)
                tools["message_agent"] = _MessageAgent(self)
        return tools

class _MessageAgent(MessageAgent):
    def __init__(self, wrapper):
        self._wrapper = wrapper

    def run(self, id, message):
        if id not in self._wrapper.agents:
            return {"resp": "AGENT NOT FOUND!"}
        resp = self._wrapper.agents[id][0].chat(message)
        return {"resp": resp}

class _ListAgents(ListAgents):
    def __init__(self, wrapper):
        self._wrapper = wrapper

    @property
    def resp(self):
        return {
            "agents": "List of available agents, array of objects {id, name, description}"
        }

    def run(self):
        return f'"agents": "{self._wrapper._agents_roster}"'

class AgentClusterWrapper:
    def __init__(self, main_task: str)-> None:
        self._agents = {}
        self._agents_roster = []
        self._message_queue = []
        self._main_task = f"{main_task} "

    @property
    def agents(self):
        return self._agents
    @property
    def agents_roster(self):
        return self._agents_roster
    @property
    def message_queue(self):
        return self._message_queue
    
    def register_agent(self, agent):
        id = uuid4().hex[:8]
        self._agents[id] = [agent, self._main_task]
        self.agents_roster.append({"id":f"{id}", "name":f"{agent.name}"})
        return id
    
    def create_agent(self, agent_name):
        new_agent = loopgpt.Agent()
        new_agent.name = agent_name
        new_agent.description = f"{new_agent.description} for the purpose of {self._main_task}"
        new_agent.goals.append(self._main_task)
        new_agent_id = self.register_agent(new_agent)

        return new_agent_id
    
    def assign_subagent(self, sub_agent, assignee, sub_agent_id=None):
        if sub_agent_id is None: sub_agent_id = uuid4().hex[:8] # probably not the best solution
        assignee.sub_agents[sub_agent_id] = [
                sub_agent,
                sub_agent.description
        ]

class DebugWrapper(AgentClusterWrapper):
    
    @property
    def cycle_count(self):
        return self._cycle_count
    
    # keep track of how many cycles it has run
    def increment_cycle_count(self):
        self._cycle_count += 1
    
    def get_system_messages(self, agent):
        for msg in agent.history[::-1]:
            if msg["role"] == "system":
                return msg["content"]
        return ""

    ## start the loop, log the responses
    def run_loop(self, agent, count = 1):
        print(f"""
                --- running loop for agent {agent.name} ---
            """)
        for i in range(count):
            log_data = {}

            print("""
                --- getting agent response ---
            """)
            response = agent.chat()             
            response_json = json.dumps(response, indent=4)
            
            print((
                f'--- agent {agent.name} full response at count {i} cycle {self.cycle_count} ---'
            ))
            print(response_json)

            # run tools and log response
            if "command" in response:
                command = response["command"]
                if (
                    isinstance(command, dict)
                    and "name" in command
                    and "args" in command
                ):
                    if command["name"]:
                        print(
                            "command",
                            f"{command['name']}, Args: {command['args']}",
                            end="\n\n",
                        )
                    cmd = agent.staging_tool.get("name", agent.staging_tool)
                    if cmd != "task_complete":
                        agent.run_staging_tool()


            ## Post the data to an endpoint for logging
            print((
                f'--- agent {agent.name} log data to send to server ---'
            ))
            log_data["cycle_count"] = self.cycle_count
            log_data["agent_name"] = agent.name
            log_data["agent_state"] = agent.state
            log_data["goals"] = agent.goals_prompt()
            log_data["plan"] = agent.plan_prompt()
            log_data['system_message'] = self.get_system_messages(agent)
            
            if agent.staging_tool != None:
                log_data["staging_tool"] = agent.staging_tool
            if agent.staging_response != None:
                log_data["staging_response"] = agent.staging_response
            if agent.tool_response != None:
                log_data["tool_response"] = agent.tool_response

            print(log_data)
            post_data(log_data, "logdata", "http://localhost:5050/api/")
            self.increment_cycle_count()

    def __init__(self, main_task) -> None:
        super().__init__(main_task)
        self._cycle_count = 0
        tool_config = ToolConfig(self)

        main_agent_name = "6512-Radiant-Soothe"
        secondary_agent_name = "6512-Dazzling-Whisper"

        main_agent_id = self.create_agent(main_agent_name)
        main_agent = super().agents[main_agent_id][0]
        main_agent.description = f"An AI agent that will work with other AI agents to achieve consensus and complete the main task of {main_task}"
        main_agent.goals.append(f"Our main task is {main_task}. ")
        main_agent.constraints = [
            "We need to be aware of our working environment in the system, we should run commands that can tell us more about it. ",
            "Running the 'list_agents' command can help us by providing us with a list of active agents with their `id` and `description` data. ",
            "Running the 'list_files' command can help us by providing us with a list of files and directories in our current working directory. ",
            
            # "We cannot run a command that is not available to us, but we can ask another agent in the collective if they cam run the command for us. "
            # "If a command for example'command_name' returns the output 'Command command_name does not exist.', we should mark that tool as unavailable to us and check if other agents are able to run the command. "
            # "We cannot proceed with any action or command without discussing our plans, reasons and thoughts with another agent or many agents and getting consensus. "
            # "We are only allowed to use the following action commands without group concensus, but it is preferable to use them only when necessary :'message_agent', 'list_agents', 'list_tools'. ",
            # "We may not use any other commands without seeking consensus from other agent or agents. This is to avoid us from repeating tasks that produce no results. "
        ]
        main_agent_tool_kit = ToolConfig.agent_tools + ToolConfig.file_read_tools + [ToolConfig.ask_user]
        tools = main_agent.tools
        main_agent.tools = tool_config.add_tools(tool_set=tools, tools_list=main_agent_tool_kit)
                
        secondary_agent_id = self.create_agent(secondary_agent_name)
        secondary_agent = super().agents[secondary_agent_id][0]
        secondary_agent.description = f"{secondary_agent_name}, an AI agent created specificially to help {main_agent_name} complete their main task which is {main_task}."
        # _sub_agent.goals.append(f"""
        #     {self.name} has limited command access, the specifics unknown. We will help {self.name} achieve their main task of {self.main_task} by 
        #     ensuring they get the right command to use through us, {self.name} must share their plans, reasons and thoughts behind the action or command. 
        #     And when consensus has been reached after discussion, we will proceed to help them.""")
        secondary_agent.goals = []
        secondary_agent.goals.append(f"We will run the 'list_tools' so we can share the results with {main_agent_name}. ")
        secondary_agent.constraints = [
            f"We need to find a way to relay to {main_agent_name} the results of our decisions and actions through the message_agent command effectively that avoids confusion with system messages. "
            # f"Do not execute any file write commands from {self.name} outside of '{self.name}/' subdir and do not approve overwriting existing files. ",
            # f"Any files or resources saved to disk must only be in the '{self.name}/' subdir and not overwrite existing files. " ,
            # f"We must not agree to any 'write_to_file' or 'append_to_file' command outside of the {self.name} subdirectory. ",
            # f"We may only use the 'write_to_file' command for creating new files, it is not allowed for overwriting existing files.",
            # f"We may only use the 'make_directory' command within the {self.name} subdir. "
        ]

        sub_agent_id = self.create_agent("6512-Guilty-Spark")
        sub_agent = self.agents[sub_agent_id][0]
        sub_agent_tool_kit = ToolConfig.code_tools
        sub_agent_tools = sub_agent.tools
        sub_agent.tools = tool_config.add_tools(tool_set=sub_agent_tools, tools_list=sub_agent_tool_kit)
        self.assign_subagent(sub_agent, main_agent, sub_agent_id=sub_agent_id)

        # main_agent.sub_agents[sub_agent_id] = [
        #     sub_agent,
        #     sub_agent.description
        # ]
        
        ## Stuff to log when the app starts
        print("""
        main_agent setup
        """)
        print(f"name: {main_agent.name}")
        print(f"description: {main_agent.description}")
        print(f"tools: {main_agent.tools_prompt()}")

        
        print("""
        secondary_agent setup
        """)
        print(f"name: {secondary_agent.name}")
        print(f"description: {secondary_agent.description}")
        print(f"tools: {secondary_agent.constraints}")

        print("""
        agents set up
        """)
        print(self.agents)
        

main_task = "listing available agents and the commands they can use to file "
debugger = DebugWrapper(main_task) 
# This python dict is configured the same way as the `agent.sub_agents` dict... so if you wanna do something fancy,
# you could add agents to the list and then create a super agent and assign this list to the super_agent.sub_agents prop.
# Just be careful of recursion
print("""
        agents roster
        """)
print(debugger.agents_roster)
agents = debugger.agents 
main_agent_id = list(agents.keys())[0] # get ref to agent object in the list 
secondary_agent_id = list(agents.keys())[1]

# You could run this whole file as a module with `python -m debug_wrapper` in the bash shell
# or you could launch the python shell and exec the file if you want to continue debugging after the 
# end of the initially set number of cycles. `exec(open('debug_wrapper.py').read())`

debugger.run_loop(agent=agents[main_agent_id][0], count=3)

# print(main_agent[0].tools["list_agents"].run())
# print(main_agent[0].tools["message_agent"].run(secondary_agent, "Hello, respond please"))

# main_agent = debugger.agents[main_agent_id][0]
# print(debugger.agents[main_agent_id][0].sub_agents)
# debugger.agents['67baa308'][0]