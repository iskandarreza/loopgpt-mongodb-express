require('dotenv').config()
const express = require('express')
const cors = require("cors")

const app = express()
const dbo = require("./conn")

app.use(cors())
app.use(
  cors({
    origin: ["POST", 'http://localhost', '*'],
    methods: ["GET", "POST"],
    allowedHeaders: ["Content-Type", "Authorization"],
  })
)
app.use(express.json({limit: '50mb'}))

app.use(require('./router'))


const PORT = process.env.PORT || 3000
app.listen(PORT, async () => {
  await dbo.connectToServer((err) => {
    if (err) {
      console.log('Error connecting to MongoDB', err)
    }

  })
  console.log(`Server listening on ${PORT}`)
})
