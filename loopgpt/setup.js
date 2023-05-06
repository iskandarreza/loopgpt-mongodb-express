const { exec } = require('child_process')

exec('pip install loopgpt --user', (err, stdout, stderr) => {
  if (err) {
    console.error(`Error installing requests module: ${err}`)
    return
  }
  console.log(`stdout: ${stdout}`)
  console.error(`stderr: ${stderr}`)
})