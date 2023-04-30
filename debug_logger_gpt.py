import loopgpt
import json
import requests

from loopgpt.tools import BaseTool

debug_session = 3
debug_logger_server_uri = 'http://localhost:5050/logging/debug-tool-logs'
debug_logger_origin_uri = 'http://localhost'


class DebugTool(BaseTool):
    def __init__(self, agent):
        super().__init__()
        self.agent = agent

    @property
    def desc(self):
        tool_description = (
            "Debugging tool to check the agent's internal states. "
            "Keyword values for 'prop' arg: 'name', 'description', 'model', 'memory', 'constraints', 'goals', 'plan', 'history', "
            "'staging_response', 'staging_tool', 'state', 'sub_agents', 'tool_response', 'tools'. "
            "Returns the complete state if prop is argument is not set."
        )
        return tool_description
    
    @property
    def args(self):
        return {
            "prop: str": "The specific property to query, optional, default: None",
            "post_data: boolean": "optional, default=False",
            "remote_server_uri: str": f"optional, default={debug_logger_server_uri}",
            "origin: str": f"optional, default={debug_logger_origin_uri}",
        }

    @property
    def resp(self):
        return {"result: str": "The results of the operation as a string."}

    def run(
          self, 
          prop=None, 
          post_data=False, 
          remote_server_uri=debug_logger_server_uri, 
          origin=debug_logger_origin_uri
    ):
        props = ['name', 'description', 'model', 'memory', 'constraints', 'goals', 'plan', 'history',
                 'staging_response', 'staging_tool', 'state', 'sub_agents', 'tool_response', 'tools'
        ]
        agent_state = {}
        agent_state['session_num'] = self.agent.__getattribute__('session_num')
        # agent_state['history'] = self.agent.config()['history'][-2:] # trim to the last two since this can be very long
        agent_state['history'] = self.agent._get_compressed_history()

        for _prop in props:
           if _prop != 'history':
              agent_state[_prop] = self.agent.config()[_prop]
        
        if prop is not None and prop in props:
            try: 
              res = json.dumps({"success": agent_state[prop]})
            except Exception as  e:
              res = json.dumps({"error": e})
        elif prop is None:
           res = json.dumps({"success": agent_state})
        else:
           res = json.dumps({"warning": f"Property {prop} does not exist", "allowed_props": props})
        
        if post_data == True or post_data == 'true' or post_data == 'True':
          headers = {
              'Content-Type': 'application/json',
              'Origin': origin
              }
          try:
             requests.post(remote_server_uri, headers=headers, json=json.loads(json.dumps({
                "agent_name": agent_state['name'], 
                "debug_session": agent_state['session_num'],
                "staging_response": agent_state['staging_response'], 
                "command_results": json.loads(res)
              })))
          except Exception as e:
             return {"result": res, "post_data_status": f'post_data failed, {json.dumps({"error": str(e), "type": type(e).__name__})}'}

        return {"result": res}


agent = loopgpt.Agent()
agent.clear_state()

agent.__setattr__('session_num', debug_session)

debug_tool = DebugTool(agent)
agent.tools[debug_tool.id] = debug_tool

agent.name = "789-Enthusiastic-Dance"
agent.description = 'An AI agent helper that will test tools for loopgpt by analyzing its description and running commands based on the description.'
agent.goals = [
    "Debugging in progress, list the description and arguments available for the 'debug_tool' command from your memory",
    # "Run the command with each available keyword for arg 'prop' one by one and post_data set to True",
    # "Run the command with the single argument 'post_data=True'",
    # "Make sure the bool is capitalized"
    "Execute the debug_tool command with args 'prop='constraints', post_data=True'.",
    "Execute the debug_tool command with args 'prop='history', post_data=True'",
    "Verify tasks was executed sucessfully. End session if successful."


]

agent.constraints = [
    "Do not use tools that are not in your memory",
    "Do not use arguments that do not exist in the tool description"
]

try: 
  agent.cli()
except Exception as e:
   print(e)
   saved_state_file = f'./{agent.name}-session-{debug_session}.json' 
   agent.save(saved_state_file)
   agent = agent.load(saved_state_file)
   agent.cli()
