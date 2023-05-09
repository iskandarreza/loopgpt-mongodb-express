require("dotenv").config() // Load environment variables from .env file
const { PythonShell } = require("python-shell")

const options = {
  mode: "text",
  pythonOptions: ["-u"], // Disable output buffering
  scriptPath: "./loopgpt-bridge",
  env: {
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,
  },
  encoding: "binary", // Set the encoding to binary
  args: [
    "--name", "3148-Graceful-Sprint",
    "--max_cycles", "1"
  ],
  timeout: 0, // run indefinitely until thread exits
}

const pyshell = new PythonShell("bridge.py", options)

pyshell.on("message", (output) => {
  try {
    if (output && JSON.parse(output)) {
      const parsed = JSON.parse(output)
      const props = ["init_state", "init_thoughts", "this_cycle", "message"]
      let categorized = false
    
      for (const prop of props) {
        if (parsed[prop]) {
          if (prop === "message") {
            console.log(parsed[prop])
          } else {
            console.log(prop, parsed[prop])            
          }
          categorized = true
        }
      }
    
      if (!categorized) {
        console.log("parsed", parsed)
      }
    }
    
    
  } catch (error) {
    console.log("Unable to parse output to JSON: ", output)
  }
})

pyshell.on("error", (err) => {
  console.error("Error from Python script:", err)
})

pyshell.end((err) => {
  if (err) throw err
  console.log("Python script finished.")
})
