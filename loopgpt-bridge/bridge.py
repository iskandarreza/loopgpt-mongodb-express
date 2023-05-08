import loopgpt
import sys
import json
import requests

sys.stdout.reconfigure(encoding='utf-8')

def post_data( data: dict, url_params: str, url: str):
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost'
    }

    json_data = json.dumps({"data": data}, sort_keys=True, indent=4)
    requests.post(f"{url}{url_params}", headers=headers, json=json.loads(json_data))

def main():
    agent = loopgpt.Agent()
    agent.name = "Node Exec Test"
    agent.goals = "Run the list_files command and then the list_agents command, then complete the task"
    agent_init_config = agent.config() # save init config

    agent.clear_state() # start fresh
    agent.from_config(agent_init_config) # reload cleared config
    agent.progress = [] # bug fix https://github.com/farizrahman4u/loopgpt/issues/41
    cycle_output = {}
    cycle_output["cycle"] = 0
    max_cycles = 3

    print(f"""
 
---------init state---------
{agent.config()}
""") 

    resp = agent.chat()
    init_resp = resp


    print(f"""
 
----------init_resp---------
{init_resp}
""") 
    

    while True:
        if isinstance(resp, str):
            cycle_output["instance"] = resp
        else:
            if "thoughts" in resp:
                msgs = {}
                thoughts = resp["thoughts"]
                if "text" in thoughts:
                    msgs[agent.name] = thoughts["text"]
                if "reasoning" in thoughts:
                    msgs["reasoning"] = thoughts["reasoning"]
                if "plan" in thoughts:
                    msgs["plan"] = (
                        thoughts["plan"].split("\n")
                        if isinstance(thoughts["plan"], str)
                        else thoughts["plan"]
                    )
                if "progress" in thoughts:
                    msgs["progress"] = thoughts["progress"]
                if "speak" in thoughts:
                    msgs["speak"] = "(voice) " + thoughts["speak"]
                # for kind, msg in msgs.items():
                    # print({kind: msg})

                cycle_output["msgs"] = msgs

            if "command" in resp:
                command = resp["command"]
                tool_results = agent.tool_response
                if (
                    isinstance(command, dict)
                    and "name" in command
                    and "args" in command
                ):
                    if command["name"]:                        
                        cycle_output["command"] = command

                    cmd = agent.staging_tool.get("name", agent.staging_tool)

                    if "name" in agent.staging_tool:
                        staging_tool = agent.staging_tool["name"]
                        cycle_output["staging_tool"] = staging_tool

                    # exit conditions
                    if cmd in ["task_complete", "ask_user"]:
                        cycle_output["tool_results"] = tool_results
                        return
                    if cycle_output["cycle"] >= max_cycles:
                        print("Max cycles reached. Terminating.")
                        return

                    # next in the chain starts here
                    resp = agent.chat(run_tool=True)
                    cycle_output["cycle"] += 1
                    cycle_output["tool_results"] = tool_results
                    cycle_output["next_resp"] = resp

                    if "command" in resp:
                        next_command = resp["command"]
                        cycle_output["next_command"] = next_command
                        
                    print(f"""
 
--------cycle_output--------
{cycle_output}""")
                    print(f"""
 
-------cycle_progress-------
{msgs["progress"]}""")
                    post_body = {}
                    url_param = "debug_logger"
                    endpoint = "http://localhost:5050/api/"
                    cycle_config = agent.config()
                    post_body["init_config"] = agent_init_config
                    post_body["init_response"] = init_resp
                    post_body["cycle_output"] = cycle_output
                    post_body["cycle_config"] = cycle_config
                    post_data(post_body, url_param, endpoint)
                    continue
            

main()
sys.stdout.flush()