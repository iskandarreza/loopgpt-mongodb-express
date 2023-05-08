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
  args: [],
  timeout: 0, // run indefinitely until thread exits
}

const pyshell = new PythonShell("bridge.py", options)

pyshell.on("message", (output) => {
  console.log("Python script output:", output)
})

pyshell.on("error", (err) => {
  console.error("Error from Python script:", err)
})

pyshell.end((err) => {
  if (err) throw err
  console.log("Python script finished.")
})
