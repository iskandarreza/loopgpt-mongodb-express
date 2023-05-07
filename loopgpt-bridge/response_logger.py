from wrappers import AgentWrapper

import json
import requests
import io
import sys

class ResponseLoggerWrapper(AgentWrapper):
    def __init__(self, url) -> None:
        super().__init__()
        self._url = url
        self._cycle_count = 0
        
    @property
    def cycle_count(self):
        return self._cycle_count
    
    # keep track of how many cycles it has run
    def increment_cycle_count(self):
        self._cycle_count += 1

    def post_data(self, data: dict, url_params: str, url: str):
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'http://localhost'
        }

        json_data = json.dumps({"data": data}, sort_keys=True, indent=4)
        requests.post(f"{url}{url_params}", headers=headers, json=json.loads(json_data))

    
    def get_system_messages(self, agent):
        for msg in agent.history[::-1]:
            if msg["role"] == "system":
                return msg["content"]
        return ""
    
    ## start the loop, log the responses
    def run_loop(self, agent, count = 1):
        buffer = io.StringIO()
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
            self.post_data(response_json, "response_json", self._url)

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
                        sys.stdout = buffer  # Redirect sys.stdout to the buffer
                        agent.run_staging_tool()
                        sys.stdout = sys.__stdout__  # Redirect sys.stdout back to the console


            ## Post the data to an endpoint for logging
            print((
                f'--- agent {agent.name} log data to send to server ---'
            ))
            log_data["cycle_count"] = self.cycle_count
            log_data["agent_name"] = agent.name
            # if agent.state != None: log_data["agent_state"] = agent.state
            log_data["goals"] = agent.goals_prompt()
            log_data["plan"] = agent.plan_prompt()
            log_data['system_message'] = self.get_system_messages(agent)
            
            if agent.staging_tool != None:
                log_data["staging_tool"] = agent.staging_tool
            if agent.staging_response != None:
                log_data["staging_response"] = agent.staging_response
            if agent.tool_response != None:
                log_data["tool_response"] = agent.tool_response

            print(json.dumps(log_data, indent=4))
            self.post_data(log_data, "logdata", self._url)
            self.increment_cycle_count()


        
        output = buffer.getvalue()
        return output
        
