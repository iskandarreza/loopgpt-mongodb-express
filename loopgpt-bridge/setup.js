const { exec } = require('child_process')

console.log(`
Installing required python packages...`)
exec('pip install loopgpt requests --user', (err, stdout, stderr) => {
  if (err) {
    console.error(`Error installing requests module: ${err}`)
    return
  }
  console.log(`stdout: ${stdout}`)
  console.error(`stderr: ${stderr}`)
})