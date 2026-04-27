const app  = require('./app');
const PORT = parseInt(process.env.PORT || '8080', 10);
app.listen(PORT, () => console.log(`Mock backend listening on :${PORT}`));
