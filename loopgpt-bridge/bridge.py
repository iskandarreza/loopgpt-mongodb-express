import loopgpt
import argparse
import sys
import json
import requests

from tool_config import ToolConfig

parser = argparse.ArgumentParser()
parser.add_argument('--name', type=str, required=True)
parser.add_argument('--max_cycles', type=int, required=True)
args = parser.parse_args()

sys.stdout.reconfigure(encoding='utf-8')


def post_data(data: dict, url_params: str, url: str):
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'http://localhost'
    }

    json_data = json.dumps({"data": data}, sort_keys=True, indent=4)
    requests.post(f"{url}{url_params}", headers=headers,
                  json=json.loads(json_data))


def main():
    agent = loopgpt.Agent()
    agent.name = f"{args.name}"
    agent.goals = "Run the list_files command and then the list_agents command, then complete the task"
    agent_init_config = agent.config()  # save init config

    # print(agent_init_config["tools"])
    agent.clear_state()  # start fresh
    agent.from_config(agent_init_config)  # reload cleared config
    agent.progress = []  # bug fix https://github.com/farizrahman4u/loopgpt/issues/41

    # trim the number of tools available
    tool_config = ToolConfig()
    custom_tool_kit = tool_config.web_tools + tool_config.agent_tools
    default_tool_set = agent.tools
    new_tool_set = tool_config.add_tools(tool_set=default_tool_set, tool_kit=custom_tool_kit)
    agent.tools.update(new_tool_set)

    cycle_output = {}
    cycle_output["cycle"] = 0
    max_cycles = int(args.max_cycles)

    print(json.dumps({"init_state": agent.config()}))

    resp = agent.chat()
    init_resp = resp

    if "thoughts" in init_resp:
        if isinstance(init_resp, dict):
            init_thoughts = init_resp["thoughts"]

            if isinstance(init_thoughts, dict):
                print(json.dumps({"init_thoughts": init_thoughts}))

    while True:

        if isinstance(resp, str):
            cycle_output["instance"] = resp  # dunno if this actually happens
        else:
            if "thoughts" in resp:
                msgs = {}
                msgs["agent"] = [{"name": agent.name, "goals": agent.goals}]
                thoughts = resp["thoughts"]
                if "text" in thoughts:
                    msgs["text"] = thoughts["text"]
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

                cycle_output["msgs"] = msgs

            if "command" in resp:
                if agent.tool_response != None:
                    tool_results = agent.tool_response
                if "name" in agent.staging_tool:
                    staging_tool = agent.staging_tool["name"]
                    cycle_output["staging_tool"] = staging_tool

                command = resp["command"]

                if (
                    isinstance(command, dict)
                    and "name" in command
                    and "args" in command
                ):
                    if command["name"]:
                        cycle_output["command"] = command

                    cmd = agent.staging_tool.get("name", agent.staging_tool)

                    # tool exit conditions
                    if cmd in ["task_complete", "ask_user"]:
                        cycle_output["tool_results"] = tool_results
                        return

                    # next in the chain starts here
                    resp = agent.chat(run_tool=True)
                    tool_results = agent.tool_response
                    cycle_output["cycle"] += 1
                    cycle_output["tool_results"] = tool_results
                    cycle_output["next_resp"] = resp

                    if "command" in resp:
                        cycle_output["next_command"] = resp["command"]

                    next_thoughts = {}
                    if "thoughts" in resp:
                        if isinstance(resp, dict):
                            if isinstance(resp["thoughts"], dict):
                                next_thoughts = resp["thoughts"]

                    this_cycle = dict({
                        "cycle": cycle_output["cycle"],
                        "cycle_progress": cycle_output["msgs"]["progress"],
                        "command": command,
                        "staging_tool": cycle_output["staging_tool"],
                        "tool_results": cycle_output["tool_results"],
                        "next_command": cycle_output["next_command"],
                        "next_thoughts": next_thoughts

                    })

                    print(json.dumps({"this_cycle": this_cycle}))

                    # cycle count exit condition
                    if cycle_output["cycle"] >= max_cycles:
                        print(json.dumps({"message": "Max cycles reached. Terminating."}))
                        return

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
