from response_logger import ResponseLoggerWrapper
import io
import sys

class Bridge(ResponseLoggerWrapper):
    def __init__(self, url) -> None:
        super().__init__(url)
        sys.stdout.reconfigure(encoding='utf-8')
        pass
    # def __init__(self, url) -> None:
        
        
    def setup_agents(self, main_task):
      
        main_agent_name = "Main Agent"
        main_agent = self.create_agent(main_agent_name)
        main_agent.description = f"An AI agent that will work with other AI agents to achieve consensus and complete the main task of {main_task}"
        main_agent.goals.append(f"Our main task is {main_task}. ")
        
        secondary_agent_name = "Support Agent"
        secondary_agent = self.create_agent(secondary_agent_name)
        secondary_agent.description = f"{secondary_agent_name}, an AI agent created specificially to help {main_agent_name} complete their main task which is {main_task}."

        self.assign_subagent(secondary_agent, main_agent)

        return main_agent
    
    def output_to_buffer(self, main_agent, count):
        buffer = io.StringIO()
        sys.stdout = buffer
        self.run_loop(main_agent, count)
        output = buffer.getvalue()
        sys.stdout = sys.__stdout__

        return output


main_task = "listing available agents and the commands they can use to file "
bridge =  Bridge("http://localhost:5050/api/")
main_agent = bridge.setup_agents(main_task)
print(bridge.run_loop(main_agent, 1))

# test_output = bridge.output_to_buffer(main_agent, 1) 
# print(test_output)


sys.stdout.flush()