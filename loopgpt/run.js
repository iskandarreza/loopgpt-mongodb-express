require('dotenv').config() // Load environment variables from .env file
const { PythonShell } = require('python-shell')

const options = {
  mode: 'text',
  pythonOptions: ['-u'], // Disable output buffering
  scriptPath: './loopgpt',
  env: {
    OPENAI_API_KEY: process.env.OPENAI_API_KEY,
  },
  // encoding: 'utf-8', // Set the encoding to utf-8
  encoding: 'binary', // Set the encoding to binary
  // args: ['--arg1', 'value1', '--arg2', 'value2'], // Pass arguments to the Python script
  args: [],
  timeout: 10000,
}

// const pyshell = new PythonShell('debug_logger_gpt.py', options)
const pyshell = new PythonShell('loopgpt-cli.py', options)


pyshell.on('message', (output) => {
  console.log('Python script output:', output)
})

pyshell.end((err) => {
  if (err) throw err
  console.log('Python script finished.')
})
