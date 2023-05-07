const express = require('express')
const router = express.Router()
const dbo = require('./conn')

const operations = async (opType, body) => {
  const db_connect = await dbo.getDb()

  if (opType === 'copy-collection-docs') {
    const collection = body.collectionName
    const destination = body.destination
    const sourceCollection = db_connect.collection(collection)
    const destCollection = db_connect.collection(destination)

    try {
      const cursor = sourceCollection.find()
      let insertedCount = 0
      await cursor.forEach(async (doc) => {
        const result = await destCollection.findOne({ _id: doc._id })
        if (result) {
          console.log(`Document with _id: ${doc._id} already exists in destination collection`)
        } else {
          const insertResult = await destCollection.insertOne(doc)
          console.log(`Inserted document with _id: ${insertResult.insertedId}`)
          insertedCount++
        }
      })
      return { status: `${insertedCount} records copied successfully` }

    } catch (error) {
      const response = { error: error }
      return response
    }


  } else if (opType === 'query') {

    const records = await db_connect
      .collection(body.collectionName)
      .aggregate(body.query)
      .toArray()

    const destCollection = await db_connect
      .collection(body.destination)
      .insertMany(records)

    if (body.destination) {
      return { insertedCount: destCollection.insertedCount }
    } else {
      return records
    }

  } else {
    return {}
  }
}

router.post('/logging/:collection', async (req, res) => {
  const routeTag = `${req.method} @/logging/${req.params.collection}`
  // console.log(`${routeTag}: ${new Date().toString()}`)
  // console.log(`${JSON.stringify(req.body, null, 4)}`)
  // console.log()
  // console.log()


  if (req.body?.operations) {

    try {
      const body = req.body
      console.log('====OPERATIONS====')
      console.log(JSON.stringify({ ...body.operations }, null, 4))
      console.log()
      console.log()

      const { type, collectionName, destination } = body.operations
      const response = await operations(type, { collectionName, destination })
      console.log(response)
      return res.status(200).json(response)

    } catch (error) {
      console.log('Error:', error)
      res.status(500).json(error)
    }

  } else {

    try {
      const db_connect = await dbo.getDb()

      let agentName
      if (req.body?.data?.name) {
        agentName = req.body.data.name
      }

      let description
      if (req.body?.data?.description) {
        description = req.body.data.description
      }

      let record = {
        ...req.body,
        dateAdded: new Date().toISOString(),
        ...(agentName && { agentName }),
        ...(description && { description }),

      }

      db_connect
        .collection(req.params.collection)
        .insertOne(record)
        .then((data) => {
          res.json(data)
          console.log(data)
        })
        .catch((e) => {
          res.json(e)
          console.log(e)
        })

    } catch (error) {
      console.log(`ERROR ${routeTag}:`, { error, body: req.body })
    }

  }

})

router.post('/ops/:type', async (req, res) => {
  try {
    const opType = req.params.type
    const body = {
      collectionName: req.body.collectionName,
      ...(req.body.query && { query: req.body.query }),
      ...(req.body.destination && { destination: req.body.destination }),
    }
    const response = await operations(opType, body)
    res.status(200).json(response)
  } catch (e) {
    console.log(e)
    res.status(500).json(e)
  }
})

router.post('/api/:endpoint', (req, res) => {
  console.log(`
  
  ${req.method} from ${req.hostname} to ${req.path}`)
  // console.log(`headers: ${
  //   JSON.stringify(req.headers,null,4)
  // }`)

  console.log(`params: ${
    JSON.stringify(req.params.endpoint,null,4)
  }`)

  console.log(`body: ${
    JSON.stringify(req.body,null,4)
  }`)

  res.status(200).send('Ok!')
})


module.exports = router

// Copy projection to a new collection
// let copyProjectionToCollection = async () => {

//   const query = [
//     { $addFields: { 'agent_name': '$data.name' } },
//     { $addFields: { 'description': '$data.description' } },

//     {
//       $project: {
//         _id: 1,
//         agent_name: 1,
//         description: 1,
//         data: 1,
//       }
//     },
//   ]


//   return fetch(
//     "http://localhost:5050/ops/query", {
//     method: 'POST',
//     headers: {
//       'Accept': 'application/json',
//       'Content-Type': 'application/json'
//     },
//     body: JSON.stringify({
//       collectionName: "state-logs",
//       query: query,
//       destination: '3698-Vivacious-Smile'
//     })
//   })
//     .then(res => res.json())
//     .then(body => console.log(body))

// }

// tool thoughts query pipeline:
// [
//   {$addFields: {
//     staging: '$data.staging_response.command.name',
//   }},
//   {$addFields: {
//     staging_thoughts: '$data.staging_response.thoughts',
//   }},
//   {$addFields: {
//     tool_args: '$data.staging_tool.args',
//   }},

//   //{ $count: 'totalDocs'}
// ]

// group by agents, total docs, last doc entries
// [
//   {
//     $project: {
//       _id: 0,
//       _docId: '$_id',
//       agentName: 1,
//       description: 1,
//       dateAdded:1,
//       data: 1,
//     }
//   },
//   {
//     $group: {
//       _id: '$data.name',
//       description: { $last: '$data.description' },
//       totalDocs: { $sum: 1 },
//       docIds: { $push: '$_docId' },
//       lastDocId: { $last: '$_docId' },
//       lastDateAdded: { $last: '$dateAdded' },
//       lastPlan: { $last: '$data.plan' },
//       lastStagingResponse: { $last: '$data.staging_response' },
//       lastStagingTool: { $last: '$data.staging_tool' },
//       lastHistory: { $last: '$data.history' },
//     }
//   },
//   //{ $count: 'totalDocs' }
// ]

