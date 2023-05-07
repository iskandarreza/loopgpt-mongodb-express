require('dotenv').config() // Load environment variables from .env file
const { PythonShell } = require('python-shell')

const options = {
  mode: 'text',
  pythonOptions: ['-u'], // Disable output buffering
  scriptPath: './loopgpt-bridge',
  env: {
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,
  },
  encoding: 'binary', // Set the encoding to binary
  args: [],
  timeout: 10000,
}

const pyshell = new PythonShell('bridge.py', options)


pyshell.on('message', (output) => {
  console.log('Python script output:', output)
})

pyshell.end((err) => {
  if (err) throw err
  console.log('Python script finished.')
})
