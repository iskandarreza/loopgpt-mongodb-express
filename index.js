require('dotenv').config()
const express = require('express')
const cors = require('cors')
const http = require('http')
const { PythonShell } = require('python-shell')

const app = express()
const dbo = require('./conn')

const server = http.createServer(app)
const io = require('socket.io')(server)

const multer = require("multer")
const upload = multer({ dest: "uploads/" })

io.engine.on('initial_headers', (headers, req) => {
  headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
})

io.engine.on('headers', (headers, req) => {
  headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
})

Object.keys(io.sockets.sockets).forEach(function (s) {
  io.sockets.sockets[s].disconnect(true)
})

app.use(cors())
app.use(
  cors({
    origin: ['POST', 'http://localhost', 'http://localhost:3000', '*'],
    methods: ['GET', 'POST'],
    allowedHeaders: ['Content-Type', 'Authorization'],
  })
)
// Set Access-Control-Allow-Origin header in response
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*')
  next()
})

app.use(express.json({ limit: '50mb' }))

app.use(require('./router'))

app.post('/start-chat', async (req, res) => {
  // Return WebSocket URL to the client
  const response = {
    websocketUrl: `http://localhost:${process.env.PORT}`,
  }
  res.status(200).json(response)
})

app.post('/restore-agent-config', (req, res) => {
  const file = req.file;
  const filePath = file.path;

  // Read the file to a const
  const data = require(filePath);

  res.send(data);
})

io.on('connection', (socket) => {
  console.log('WebSocket client connected with ID:', socket.id)

  socket.on('start', (message) => {
    // Set the options object with the arguments
    const { name, max_cycles, goals, constraints } = message

    const options = {
      mode: 'text',
      pythonOptions: ['-u'],
      scriptPath: 'loopgpt-bridge',
      env: {
        OPENAI_API_KEY: process.env.OPENAI_API_KEY,
      },
      encoding: 'binary',
      args: [
        '--name',
        name,
        '--max_cycles',
        max_cycles,
        '--goals',
        goals,
        '--constraints',
        constraints,
      ],
      timeout: 0,
    }

    runPythonScript(options, socket)
  })

  socket.on('disconnect', () => {
    console.log('WebSocket client disconnected with ID:', socket.id)
  })
})

const PORT = process.env.PORT || 3000
server.listen(PORT, async () => {
  await dbo.connectToServer((err) => {
    if (err) {
      console.log('Error connecting to MongoDB', err)
    }
  })
  console.log(`Server listening on ${PORT}`)
})

function runPythonScript(options, socket) {
  const pyshell = new PythonShell('bridge.py', options)
  pyshell.on('message', (output) => {
    try {
      if (output && JSON.parse(output)) {
        const parsed = JSON.parse(output)
        const props = ['init_state', 'init_thoughts', 'this_cycle', 'current_state', 'message']
        let categorized = false

        for (const prop of props) {
          if (parsed[prop]) {
            socket.emit(prop, parsed[prop])
            console.log(prop, parsed[prop])
            categorized = true
          }
        }

        if (!categorized) {
          socket.emit('parsed', parsed)
          console.log('parsed', parsed)
        }
      }
    } catch (error) {
      socket.emit('error', 'Unable to parse output to JSON: ' + output)
      console.log('Unable to parse output to JSON: ', output)

      pyshell.end((err) => {
        if (err) throw err
        console.log('Python script finished.')
      })
    }
  })

  pyshell.on('error', (err) => {
    socket.emit('error', 'Error from Python script: ' + err)
    console.error('Error from Python script:', err)
  })

  pyshell.end((err) => {
    if (err) throw err
    console.log('Python script finished.')
    socket.disconnect()
  })
}
