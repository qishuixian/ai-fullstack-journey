const express = require('express');

const app = express();

const port = 3001;

// ✅ 添加 CORS 支持

app.use((req, res, next) => {

res.header('Access-Control-Allow-Origin', '*');

res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');

res.header('Access-Control-Allow-Headers', 'Content-Type');

next();

});

app.get('/time', (req, res) => {

const now = new Date();

res.send(now.toLocaleString());

});

app.listen(port, () => {

console.log(`Backend listening at http://localhost:${port}`);

});