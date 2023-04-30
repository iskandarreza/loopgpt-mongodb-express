const express = require('express')
const router = express.Router()
const dbo = require('./conn')

router.post('/logging/:collection', async (req, res) => {
  const routeTag = `${req.method} @/logging/${req.params.collection}`
  console.log(`${routeTag}: ${new Date().toString()}`)
  console.log(`${JSON.stringify(req.body, null, 4)}`)

  const db_connect = await dbo.getDb()

  try {
    db_connect
      .collection(req.params.collection)
      .insertOne(req.body)
      .then((data) => {
        res.json(data)
      })
      .catch((e) => {
        res.status(500).json(e)
      })
  } catch (error) {
    console.log(`ERROR ${routeTag}:`, { error, body: req.body })
  }
  
})

module.exports = router
